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
    FROM_RACE_FORMAT = ''
    LAST_HEAT_POSITION = 'Last_Heat_Position'
    BRACKETS = 'Brackets'

class Generator:
    RANDOM_FILL = "Balanced_random_fill"
    RANKED_FILL = "Ranked_fill"
    BUMP_UP = "Ladder"
    BRACKET_SINGLE_ELIMINATION = "Regulation_bracket__single_elimination"
    BRACKET_DOUBLE_ELIMINATION = "Regulation_bracket__double_elimination"
    BRACKET_DOUBLE_ELIMINATION_8 = "_8_Pilot_Double_Elimination_Bracket"

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
        event_name = request.json.get("name")
        pilots = request.json.get("pilots")
        freeHeatSize = request.json.get("settings").get("freeHeatSize")
        qualHeatSize = request.json.get("settings").get("qualHeatSize")
        finalType = request.json.get("settings").get("finalType")
        numAdvance = request.json.get("settings").get("numAdvance")
        finalHeatSize = request.json.get("settings").get("finalHeatSize")

        ### PROVE LIBERE ###

        # creazione classe prove libere
        free_practice_class = rhapi.db.raceclass_add(
            name = "Prove libere",
            description = "Generata automaticamente dal plugin",
            raceformat = RaceFormat.FASTEST_LAP_QUALIFIER,
            win_condition = Ranking.FROM_RACE_FORMAT,
            rounds = 0,
            heat_advance_type = 1,
            round_type = 0
        )
        rhapi.db.raceclass_alter(free_practice_class.id, attributes = {
            "orchestrator_event_name": event_name,
            "orchestrator_class_type": "free_practice"
        })

        # creazione heat prove libere
        heats = []
        total_pilots = len(pilots)
        num_heats = (total_pilots + freeHeatSize - 1) // freeHeatSize  # divisione arrotondata in su
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
            "total_pilots": total_pilots,
            "seed_offset": 1,
            "suffix": "Qualifier"
        })

        # configurazione ranking
        rhapi.db.raceclass_alter(qualifier_class,
            name = "Qualifiche",
            description = "Generata automaticamente dal plugin",
            raceformat = RaceFormat.FASTEST_CONSECUTIVE_LAPS_QUALIFIER,
            win_condition = Ranking.FROM_RACE_FORMAT,
            rounds = 0,
            heat_advance_type = 1,
            round_type = 0,
            attributes = {
                "orchestrator_event_name": event_name,
                "orchestrator_class_type": "qualifier"
            }
        )

        ### FINALI ###

        #if final_type == "16":
        # TODO: gestire il caso 8 piloti

        # creazione classe finali tramite generatore
        final_class = rhapi.heatgen.generate(Generator.BRACKET_DOUBLE_ELIMINATION, {
            "input_class": qualifier_class,
            "output_class": None,
            "standard": "multigp16",
            "seed_offset": 1
        })

        # configurazione ranking
        rhapi.db.raceclass_alter(final_class,
            name = "Finali",
            description = "Generata automaticamente dal plugin",
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
                "orchestrator_event_name": event_name,
                "orchestrator_class_type": "final"
            }
        )

        # rinominazione heat finali
        heats = rhapi.db.heats_by_class(final_class)
        for heat in heats:
            name = heat.name
            if ':' in name:
                new_name = name[:name.index(':')]
                rhapi.db.heat_alter(heat.id, name=new_name)

        ### FINALINE ###

        if total_pilots > 16:
            # TODO: gestire il caso 8 piloti

            # creazione classe finaline tramite generatore
            small_final_class = rhapi.heatgen.generate(Generator.BUMP_UP, {
                "input_class": qualifier_class,
                "output_class": None,
                "advances_per_heat": numAdvance,
                "qualifiers_per_heat": finalHeatSize,
                "total_pilots": total_pilots - 14, # TODO: adattare per 8 piloti
                "seed_offset": 15, # TODO: adattare per 8 piloti
                "suffix": "Main"
            })

            # configurazione ranking
            rhapi.db.raceclass_alter(small_final_class,
                name = "Finaline",
                description = "Generata automaticamente dal plugin",
                raceformat = RaceFormat.FIRST_TO_3_LAPS,
                win_condition = Ranking.LAST_HEAT_POSITION,
                rounds = 0,
                heat_advance_type = 1,
                round_type = 0,
                attributes = {
                    "orchestrator_event_name": event_name,
                    "orchestrator_class_type": "small_final"
                }
            )
            
            # inserimento dei vincitori delle finaline nelle finali
            heats = rhapi.db.heats_by_class(final_class)
            for heat in heats:
                slots = rhapi.db.slots_by_heat(heat.id)
                slot = slots[node_index]
                for slot in slots:
                    # TODO: adattare a 8 piloti
                    if slot.seed_rank == 15:
                        rhapi.db.slot_alter(slot.id,
                            method = ProgramMethod.CLASS_RESULT,
                            seed_raceclass_id = small_final_class,
                            seed_rank = 1
                        )
                    if slot.seed_rank == 16:
                        rhapi.db.slot_alter(slot.id,
                            method = ProgramMethod.CLASS_RESULT,
                            seed_raceclass_id = small_final_class,
                            seed_rank = 2
                        )

        return jsonify({"success": True})

    rhapi.ui.blueprint_add(bp)

    rhapi.ui.register_panel("orchestrator", "CSI Toolkit Panel", "settings")
    rhapi.ui.register_markdown("orchestrator", "CSI Toolkit Panel link", "Race administrator panel is available [here](/orchestrator)")
    
    rhapi.fields.register_raceclass_attribute(UIField('orchestrator_event_name', "Event Name", UIFieldType.TEXT, value="", private=True))
    rhapi.fields.register_raceclass_attribute(UIField('orchestrator_class_type', "Class Type", UIFieldType.TEXT, value="", private=True))
