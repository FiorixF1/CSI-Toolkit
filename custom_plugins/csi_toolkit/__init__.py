import logging
import random
import RHUtils
from eventmanager import Evt

from Database import ProgramMethod
from RHUI import UIField, UIFieldType, UIFieldSelectOption

from flask import jsonify, request, templating
from flask.blueprints import Blueprint

from .class_rank_brackets.class_rank_brackets     import initialize as class_rank_brackets_initializer
from .csi_export.csi_export                       import initialize as csi_export_initializer
from .ddr_overlays.ddr_overlays                   import initialize as ddr_overlays_initializer
from .generator_8_pilots_de.generator_8_pilots_de import initialize as generator_8_pilots_de_initializer

logger = logging.getLogger(__name__)



class RaceFormat:
    FIRST_TO_3_LAPS = 4
    FASTEST_LAP_QUALIFIER = 6
    FASTEST_CONSECUTIVE_LAPS_QUALIFIER = 7

class Ranking:
    FROM_RACE_FORMAT = ""
    LAST_HEAT_POSITION = "Last_Heat_Position"
    BRACKETS = "Brackets"

class Generator:
    RANDOM_FILL = "Balanced_random_fill"
    RANKED_FILL = "Ranked_fill"
    BUMP_UP = "Ladder"
    BRACKET_SINGLE_ELIMINATION = "Regulation_bracket__single_elimination"
    BRACKET_DOUBLE_ELIMINATION = "Regulation_bracket__double_elimination"
    BRACKET_DOUBLE_ELIMINATION_8 = "_8_Pilot_Double_Elimination_Bracket"

class ClassType:
    FREE_PRACTICE = "free_practice"
    QUALIFIER = "qualifier"
    FINAL = "final"
    SMALL_FINAL = "small_final"



def initialize(rhapi):
    class_rank_brackets_initializer(rhapi)
    csi_export_initializer(rhapi)
    ddr_overlays_initializer(rhapi)
    generator_8_pilots_de_initializer(rhapi)

    bp = Blueprint(
        'orchestrator',
        __name__,
        template_folder='orchestrator/pages',
        static_folder='orchestrator/static',
        static_url_path='/csi_toolkit/orchestrator/static'
    )

    ### home page ###
    @bp.route('/orchestrator')
    def orchestrator_homePage():
        return templating.render_template('orchestrator_index.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__)

    @bp.route("/orchestrator/create_event", methods=["POST"])
    def create_event():
        ### LETTURA PARAMETRI + ERROR HANDLING ###

        if any(map(lambda x: x not in request.json, ["eventName", "pilots", "settings"])):
            return jsonify({
                "success": False,
                "error": "Richiesta malformata"
            })

        eventName = request.json["eventName"]
        pilots = request.json["pilots"]
        freeHeatSize = request.json["settings"].get("freeHeatSize", 4)
        qualHeatSize = request.json["settings"].get("qualHeatSize", 4)
        finalType = request.json["settings"].get("finalType", 16)
        numAdvance = request.json["settings"].get("numAdvance", 2)
        finalHeatSize = request.json["settings"].get("finalHeatSize", 4)

        if not eventName:
            return jsonify({
                "success": False,
                "error": "invalid eventName"
            })

        for raceclass in rhapi.db.raceclasses:
            if rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_event_name") == eventName:
                return jsonify({
                    "success": False,
                    "error": "Esiste già un evento con questo nome"
                })
        
        if freeHeatSize not in [3, 4, 5, 6]:
            return jsonify({
                "success": False,
                "error": "invalid freeHeatSize"
            })

        if len(pilots) < 2:
            return jsonify({
                "success": False,
                "error": "invalid pilots"
            })

        if qualHeatSize not in [3, 4, 5, 6]:
            return jsonify({
                "success": False,
                "error": "invalid qualHeatSize"
            })

        if finalType not in [8, 16]:
            return jsonify({
                "success": False,
                "error": "invalid finalType"
            })

        if numAdvance not in [1, 2, 3, 4]:
            return jsonify({
                "success": False,
                "error": "invalid numAdvance"
            })

        if finalHeatSize not in [2, 3, 4, 5, 6] or numAdvance >= finalHeatSize:
            return jsonify({
                "success": False,
                "error": "invalid finalHeatSize"
            })

        ### PROVE LIBERE ###

        # creazione classe prove libere
        free_practice_class = rhapi.db.raceclass_add(
            name = f"{eventName} - Prove libere",
            description = "",
            raceformat = RaceFormat.FASTEST_LAP_QUALIFIER,
            win_condition = Ranking.FROM_RACE_FORMAT,
            rounds = 0,
            heat_advance_type = 1,
            round_type = 0
        )
        rhapi.db.raceclass_alter(free_practice_class.id, attributes = {
            "orchestrator_event_name": eventName,
            "orchestrator_class_type": ClassType.FREE_PRACTICE
        })

        # creazione heat prove libere
        heats = []
        num_pilots = len(pilots)
        num_heats = (num_pilots + freeHeatSize - 1) // freeHeatSize  # divisione arrotondata in su
        for i in range(num_heats):
            heat_name = f"Heat {i+1}"
            heat = rhapi.db.heat_add(
                name = heat_name,
                raceclass = free_practice_class.id
            )
            heats.append(heat)

        # assegna i piloti alle heat
        randomized_pilots = pilots[::]
        random.shuffle(randomized_pilots)
        for i, pilot in enumerate(randomized_pilots):
            # TODO: evitare heat da 1 o 2 piloti "prelevando" piloti da altre heat piene
            heat_index = i // freeHeatSize
            node_index = i % freeHeatSize  # posizioni 0..freeHeatSize-1

            slots = rhapi.db.slots_by_heat(heats[heat_index].id)
            slot = slots[node_index]

            rhapi.db.slot_alter(slot.id,
                method = ProgramMethod.ASSIGN,
                pilot = pilot["id"]
            )

        ### QUALIFICHE ###

        # creazione classe qualifiche tramite generatore
        qualifier_class = rhapi.heatgen.generate(Generator.RANKED_FILL, {
            "input_class": free_practice_class.id,
            "output_class": None,
            "qualifiers_per_heat": qualHeatSize, 
            "num_pilots": num_pilots,
            "seed_offset": 1,
            "suffix": "Qualifier"
        })

        # configurazione ranking
        rhapi.db.raceclass_alter(qualifier_class,
            name = f"{eventName} - Qualifiche",
            description = "",
            raceformat = RaceFormat.FASTEST_CONSECUTIVE_LAPS_QUALIFIER,
            win_condition = Ranking.FROM_RACE_FORMAT,
            rounds = 0,
            heat_advance_type = 1,
            round_type = 0,
            attributes = {
                "orchestrator_event_name": eventName,
                "orchestrator_class_type": ClassType.QUALIFIER
            }
        )

        ### FINALI ###

        # creazione classe finali tramite generatore
        if finalType == 16:
            # multigp16
            final_class = rhapi.heatgen.generate(Generator.BRACKET_DOUBLE_ELIMINATION, {
                "input_class": qualifier_class,
                "output_class": None,
                "standard": "multigp16",
                "seed_offset": 1
            })
        elif finalType == 8:
            # ddr8de
            final_class = rhapi.heatgen.generate(Generator.BRACKET_DOUBLE_ELIMINATION_8, {
                "input_class": qualifier_class,
                "output_class": None
            })
        else:
            pass
        # due piloti provengono dalle finaline, gli altri sono qualificati alla finale
        already_qualified = finalType - 2

        # configurazione ranking
        rhapi.db.raceclass_alter(final_class,
            name = f"{eventName} - Finali",
            description = "",
            raceformat = RaceFormat.FIRST_TO_3_LAPS,
            win_condition = Ranking.BRACKETS,
            rank_settings = {
                "bracket_type": "CSI Drone Racing",
                "qualifier_class": qualifier_class,
                "chase_the_ace": True,
                "iron_man": True
            },
            rounds = 0,
            heat_advance_type = 1,
            round_type = 0,
            attributes = {
                "orchestrator_event_name": eventName,
                "orchestrator_class_type": ClassType.FINAL
            }
        )

        # rinominazione heat finali (lascia solo "Race x")
        heats = rhapi.db.heats_by_class(final_class)
        for heat in heats:
            name = heat.name
            if ':' in name:
                new_name = name[:name.index(':')]
                rhapi.db.heat_alter(heat.id, name=new_name)
            if '-' in name:
                new_name = name[:name.index('-')]
                rhapi.db.heat_alter(heat.id, name=new_name)

        ### FINALINE ###

        if num_pilots > finalType:
            # TODO: gestire il caso di finaline effettivamente inserite (il race manager potrebbe non volerle fare)

            # creazione classe finaline tramite generatore (funziona sia con multigp16 che ddr8de)
            small_final_class = rhapi.heatgen.generate(Generator.BUMP_UP, {
                "input_class": qualifier_class,
                "output_class": None,
                "advances_per_heat": numAdvance,
                "qualifiers_per_heat": finalHeatSize,
                "num_pilots": num_pilots - already_qualified,
                "seed_offset": already_qualified + 1,
                "suffix": "Main"
            })

            # configurazione ranking
            rhapi.db.raceclass_alter(small_final_class,
                name = f"{eventName} - Finaline",
                description = "",
                raceformat = RaceFormat.FIRST_TO_3_LAPS,
                win_condition = Ranking.LAST_HEAT_POSITION,
                rounds = 0,
                heat_advance_type = 1,
                round_type = 0,
                attributes = {
                    "orchestrator_event_name": eventName,
                    "orchestrator_class_type": ClassType.SMALL_FINAL
                }
            )

            # inserimento dei vincitori delle finaline nelle finali
            heats = rhapi.db.heats_by_class(final_class)
            for heat in heats:
                slots = rhapi.db.slots_by_heat(heat.id)
                slot = slots[node_index]
                for slot in slots:
                    # vincitore finaline
                    if slot.seed_rank == already_qualified+1:
                        rhapi.db.slot_alter(slot.id,
                            method = ProgramMethod.CLASS_RESULT,
                            seed_raceclass_id = small_final_class,
                            seed_rank = 1
                        )
                    # secondo classificato finaline
                    if slot.seed_rank == already_qualified+2:
                        rhapi.db.slot_alter(slot.id,
                            method = ProgramMethod.CLASS_RESULT,
                            seed_raceclass_id = small_final_class,
                            seed_rank = 2
                        )

        rhapi.ui.broadcast_raceclasses()
        rhapi.ui.broadcast_heats()

        return jsonify({
            "success": True,
            "data": dict()
        })

    @bp.route("/orchestrator/get_events")
    def get_events():
        events = dict()
        for raceclass in rhapi.db.raceclasses:
            event_name = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_event_name")
            class_type = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_class_type")
            if event_name:
                if not events.get(event_name):
                    events[event_name] = {
                        "name": event_name,
                        "classes": dict(),
                        "bracket_type": 'none'
                    }
                events[event_name]["classes"][class_type] = {
                    "id": raceclass.id,
                    "name": raceclass.name
                }
                # ricava il tipo di finale
                if class_type == ClassType.FINAL:
                    number_of_final_heats = len(rhapi.db.heats_by_class(raceclass.id))
                    if number_of_final_heats == 14:
                        events[event_name]["bracket_type"] = 'multigp16'
                    elif number_of_final_heats == 6:
                        events[event_name]["bracket_type"] = 'ddr8de'
                    else:
                        events[event_name]["bracket_type"] = 'none'

        result = []
        for event_name in events:
            this_event = {
                "name": event_name,
                "bracket_type": events[event_name].pop("bracket_type"),
                "classes": events[event_name].pop("classes"),
            }
            result.append(this_event)

        return jsonify({
            "success": True,
            "data": result
        })

    @bp.route("/orchestrator/delete_event", methods=["POST"])
    def delete_event():
        eventName = request.json.get("eventName")

        if not eventName:
            return jsonify({
                "success": False,
                "error": "invalid eventName"
            })

        classes_to_remove = dict()
        for raceclass in rhapi.db.raceclasses:
            event_name = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_event_name")
            class_type = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_class_type")
            if event_name == eventName:
                heats = rhapi.db.heats_by_class(raceclass.id)
                for heat in heats:
                    rhapi.db.heat_delete(heat)
                rhapi.db.raceclass_delete(raceclass.id)

        rhapi.ui.broadcast_raceclasses()
        rhapi.ui.broadcast_heats()

        return jsonify({
            "success": True,
            "data": dict()
        })

    @bp.route("/orchestrator/export_results", methods=["POST"])
    def export_results():
        eventName = request.json.get("eventName")

        if not eventName:
            return jsonify({
                "success": False,
                "error": "invalid eventName"
            })

        # identifica classi dell'evento per configurare l'esportatore
        rhapi.db.option_set('csi_small_final', '0')
        for raceclass in rhapi.db.raceclasses:
            event_name = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_event_name")
            class_type = rhapi.db.raceclass_attribute_value(raceclass, "orchestrator_class_type")
            if event_name == eventName:
                if class_type == ClassType.QUALIFIER:
                    rhapi.db.option_set('qualifier_class', raceclass.id)
                elif class_type == ClassType.FINAL:
                    rhapi.db.option_set('final_class', raceclass.id)
                elif class_type == ClassType.SMALL_FINAL:
                    # TODO: gestire il caso in cui il race director non vuole fare le finaline
                    rhapi.db.option_set('small_final_class', raceclass.id)
                    rhapi.db.option_set('csi_small_final', '1')
                    
        # lancia l'esportatore
        result = rhapi.io.run_export("CSV_CSI_Upload")

        return jsonify({
            "success": True,
            "data": result
        })

    rhapi.ui.blueprint_add(bp)

    rhapi.ui.register_panel("orchestrator", "CSI Toolkit Panel", "settings")
    rhapi.ui.register_markdown("orchestrator", "CSI Toolkit Panel link", "Race administrator panel is available [here](/orchestrator)")
    
    rhapi.fields.register_raceclass_attribute(UIField('orchestrator_event_name', "Event Name", UIFieldType.TEXT, value="", private=True))
    rhapi.fields.register_raceclass_attribute(UIField('orchestrator_class_type', "Class Type", UIFieldType.TEXT, value="", private=True))
