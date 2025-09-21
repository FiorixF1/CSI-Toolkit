import csv
import io
import json
import logging
import requests
from data_export import DataExporter
#from sqlalchemy.ext.declarative import DeclarativeMeta
#from sqlalchemy import inspect
import re
from RHUI import UIField, UIFieldType, UIFieldSelectOption

class CSIExport():
    CSI_VERSION = "x.y.z"
    CSI_API_ENDPOINT = "https://api.abcdef.com"
    CSI_API_VERSION = "x.y.z"
    CSI_UPDATE_REQ = False
    
    def __init__(self, rhapi):
        self.logger = logging.getLogger(__name__)
        self._rhapi = rhapi

    def init_plugin(self, args):
        #isEnabled = self.isEnabled()
        #isConnected = self.isConnected()
        #notEmptyKeys = self.getEventUUID()["notempty"]

        #if isEnabled is False:
        #    self.logger.warning("FPVScores.com Sync is disabled. Please enable on the Format page")
        #elif notEmptyKeys is False:
        #    self.logger.warning("FPVScores.com Event UUID is empty. Please register at https://fpvscores.com")
        #elif isConnected is False:
        #    self.logger.warning("It looks like your RotorHazard timer is not connected to the internet. Check connection and try again.")
        #else:
        #    x = requests.get(self.CSI__API_ENDPOINT+'/versioncheck.php?version='+self.CSI_VERSION)
        #    respond = x.json()
        #    if self.CSI_VERSION != respond["version"]:
        #        if respond["softupgrade"] == True:
        #            self.logger.warning("New version of FPVScores.com Sync Plugin is available. Please consider upgrading.")

        #        if respond["forceupgrade"] == True:
        #            self.logger.warning("FPVScores.com Sync Plugin needs to be updated.")
        #            self.CSI_UPDATE_REQ = True

        #    self.logger.info("FPVScores.com Sync is ready")
        
        self.init_ui(args)

    def init_ui(self, args):
        ui = self._rhapi.ui
        ui.register_panel("csi_export_panel", "CSI Export Settings", "format")

        classes = self._rhapi.db.raceclasses
        options = []
        for this_class in classes:
            if not this_class.name:
                name = f"Class {this_class.id}"
            else:
                name = this_class.name
            options.append(UIFieldSelectOption(this_class.id, name))
        if len(options) > 0:
            default_class = options[0].value
        else:
            default_class = 0

        ui_csi_qualifier = UIField(name = "qualifier_class",
                                   label = "Qualifier class",
                                   field_type = UIFieldType.SELECT,
                                   options = options,
                                   value = default_class,
                                   desc = "Class used in qualification stage")
        ui_csi_final = UIField(name = "final_class",
                               label = "Final class",
                               field_type = UIFieldType.SELECT,
                               options = options,
                               value = default_class,
                               desc = "Class used in final stage")
        
        fields = self._rhapi.fields
        fields.register_option(ui_csi_qualifier, "csi_export_panel")
        fields.register_option(ui_csi_final, "csi_export_panel")

        ui_csi_enable_small_final = UIField(name = "csi_small_final", label = "Enable Small Final", field_type = UIFieldType.CHECKBOX, value = True, desc = "Enable if small final heats are scheduled")
        ui_csi_small_final = UIField(name = "small_final_class",
                                     label = "Small final class",
                                     field_type = UIFieldType.SELECT,
                                     options = options,
                                     value = default_class,
                                     desc = "Class used in small final stage (if enabled)")
        fields.register_option(ui_csi_enable_small_final, "csi_export_panel")
        fields.register_option(ui_csi_small_final, "csi_export_panel")
        
        #ui_csi_autosync = UIField(name = "csi_autoupload", label = "Enable Automatic Sync", field_type = UIFieldType.CHECKBOX, desc = "Enable or disable automatic syncing. A network connection is required.")
        #ui_csi_event_uuid = UIField(name = "csi_event_uuid", label = "FPV Scores Event UUID", field_type = UIFieldType.TEXT, desc = "Event UUID obtainable from FPVScores.com")

        #fields.register_option(ui_csi_autosync, "csi_export_panel")
        #fields.register_option(ui_csi_event_uuid, "csi_export_panel")

        #ui.register_quickbutton("csi_export_panel", "csi_export_leaderboard", "Export Final Leaderboard", self.exportFinalLeaderboard, {'rhapi': self._rhapi})
        #ui.register_quickbutton("csi_export_panel", "csi_syncpilots", "Full Manual Sync", self.runFullManualSyncBtn, {'rhapi': self._rhapi})
        #ui.register_quickbutton("csi_export_panel", "csi_clear", "Clear event data on FPVScores.com", self.runClearBtn, {'rhapi': self._rhapi})

        self._rhapi.ui.broadcast_ui("format")

        #fields.register_pilot_attribute( self.country_ui_field )
        #fields.register_pilot_attribute( UIField('safetycheck', "Safety Checked", UIFieldType.CHECKBOX) )
        #fields.register_pilot_attribute( UIField('fpvs_uuid', "FPVS Pilot UUID", UIFieldType.TEXT) )
        #fields.register_pilot_attribute( UIField('comm_elrs', "ELRS Passphrase", UIFieldType.TEXT) )
        #fields.register_pilot_attribute( UIField('comm_tbs_mac', "Fusion MAC Address", UIFieldType.TEXT) )

        #ui.register_quickbutton("csi_export_panel", "csi_downloadavatars", "Download Pilot Avatars", self.runDownloadAvatarsBtn, {'rhapi': self._rhapi})

    def isConnected(self):
        try:
            response = requests.get(self.CSI_API_ENDPOINT, timeout=5)
            return True
        except requests.ConnectionError:
            return False 

    def isEnabled(self):
        enabled = self._rhapi.db.option("csi_autoupload")
        if enabled == "1" and self.CSI_UPDATE_REQ == False:
            return True
        else:
            if self.CSI_UPDATE_REQ == True:
                self.logger.warning("FPVScores requires a mandatory update. Please update and restart the timer. No results will be synced for now.")
            return False

    def getEventUUID(self):
        event_uuid = self._rhapi.db.option("csi_event_uuid")
        notempty = True if (event_uuid) else False
        keys = {
            "notempty": notempty,
            "event_uuid": event_uuid,
        }
        return keys

    # esempio di push in caso di eventi
    def class_listener(self, args):
        rhapi = self._rhapi
        
        keys = self.getEventUUID()
        if self.isConnected() and self.isEnabled() and keys["notempty"]:
            eventname = args["_eventName"]
            if eventname == "classAdd":
                classid = args["class_id"]
                classname = "Class " + str(classid)
                brackettype = "none"
                classdescription = "No description"
            elif eventname == "classAlter":
                classid = args["class_id"]
                raceclass = self._rhapi.db.raceclass_by_id(classid)
                classname = raceclass.name
                classdescription = raceclass.description
                brackettype = "check"
            elif eventname == "heatGenerate":
                classid = args["output_class_id"]
                raceclass = self._rhapi.db.raceclass_by_id(classid)
                if raceclass.name == "":
                    classname = "Class " + str(classid)
                else:
                    classname = raceclass.name
                classdescription = raceclass.description
                brackettype = self.get_brackettype(args)
            payload = {
                "event_uuid": keys["event_uuid"],
                "class_id": classid,
                "class_name": classname,
                "class_descr": classdescription,
                "class_bracket_type": brackettype,
                "event_name": eventname
            }
            x = requests.post(self.CSI_API_ENDPOINT+"/rh/"+self.CSI_API_VERSION+"/?action=class_update", json = payload)
            self.UI_Message(rhapi,x.text)
        else:
            self.logger.warning("FPVScores.com Sync Disabled")

    def get_brackettype(self, args):
        brackettype = args["generator"]      
        if brackettype == "Regulation_bracket__double_elimination" or brackettype == "Regulation_bracket__single_elimination":
            generate_args = args["generate_args"]
            brackettype = brackettype+"_"+generate_args["standard"]    
        return brackettype

    def UI_Message(self, rhapi, text):
        try:
            parsed_text = json.loads(text)
            # Check if it's a list and get the first item
            if isinstance(parsed_text, list):
                parsed_text = parsed_text[0]

            # Check for "status" and "message" keys
            if "status" in parsed_text and "message" in parsed_text:
                if parsed_text["status"] == "error":
                    rhapi.ui.message_notify(rhapi.__("FPVScores: " + parsed_text["message"]))
                else:
                    rhapi.ui.message_notify(rhapi.__("FPVScores: " + parsed_text["message"]))
            else:
                rhapi.ui.message_notify(rhapi.__("FPVScores: Unexpected response format."))
        except json.JSONDecodeError:
            rhapi.ui.message_notify(rhapi.__("FPVScores: Failed to parse server response."))

    # ... #
    
    def getGroupingDetails(self, heatobj, db):
        heatname = str(heatobj.name)
        heatid = str(heatobj.id)

        if heatname == "None" or heatname == "":
            heatname = "Heat " + heatid

        heatclassid = str(heatobj.class_id)
        racechannels = self.getRaceChannels()

        thisheat = {
            "class_id": heatclassid,
            "class_name": "unsupported",
            "class_descr": "unsupported",
            "class_bracket_type": "",
            "heat_name": heatname,
            "heat_id": heatid,
            "slots": []
        }
        slots = db.slots_by_heat(heatid)
        
        for slot in slots:
            if slot.node_index is not None:
                channel = racechannels[slot.node_index] 
                pilotcallsign = "-"
                if slot.pilot_id != 0:               
                    pilot = db.pilot_by_id(slot.pilot_id)
                    pilotcallsign = pilot.callsign
                thisslot = {
                    "pilotid": slot.pilot_id,
                    "nodeindex": slot.node_index,
                    "channel": channel,
                    "callsign": pilotcallsign
                }

                if (thisslot["channel"] != "0" and thisslot["channel"] != "00"):
                    thisheat["slots"].append(thisslot)
        return thisheat

    def getRaceChannels(self):
        frequencies = self._rhapi.race.frequencyset.frequencies
        freq = json.loads(frequencies)
        bands = freq["b"]
        channels = freq["c"]
        racechannels = []
        for i, band in enumerate(bands):
            racechannel = "0"
            if str(band) == 'None':
                racechannels.insert(i,racechannel)
            else:
                channel = channels[i]
                racechannel = str(band) + str(channel)
                racechannels.insert(i,racechannel)
        
        return racechannels

    def runClearBtn(self):
        rhapi = self._rhapi
        keys = self.getEventUUID()
        payload = {
            "event_uuid": keys["event_uuid"],
        }
        x = requests.post(self.CSI_API_ENDPOINT+"/rh/"+self.CSI_API_VERSION+"/?action=rh_clear", json = payload)
        print(x.text)
        self.UI_Message(rhapi, x.text)
        
    def runFullManualSyncBtn(self, args):
        rhapi = self._rhapi
        data = rhapi.io.run_export('JSON_FPVScores_Upload')
        self.uploadToFPVS_frombtn(data)

    def uploadToFPVS_frombtn(self, input_data):
        rhapi = self._rhapi
        json_data =  input_data['data']
        url = self.CSI_API_ENDPOINT+"/rh/"+self.CSI_API_VERSION+"/?action=full_manual_import"
        headers = {'Authorization' : 'rhconnect', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
        r = requests.post(url, data=json_data, headers=headers)
        self.UI_Message(rhapi, r.text)
        print(r.text)

    def generate_results_for_class(self, class_id):
        raceclass = self._rhapi.db.raceclass_by_id(class_id)
        ranking = raceclass.ranking

        rankpayload = dict()
        if ranking != None:
            if isinstance(ranking, bool) and ranking is False:
                rankpayload = dict()
            else:
                meta = ranking["meta"]
                method_label = meta["method_label"]
                ranks = ranking["ranking"]
                for rank in ranks:
                    rank_values = rank.copy()

                    pilot_id = rank_values.pop("pilot_id", None)
                    callsign = rank_values.pop("callsign", None)
                    position = rank_values.pop("position", None)
                    # team_name = rank_values.pop("team_name", None)
                    # node = rank_values.pop("node", None)
                    # total_time_laps = rank_values.pop("total_time_laps", None)
                    # heat = rank_values.pop("heat", None)

                    pilot = {
                        "classid": class_id,
                        "classname": raceclass.name,
                        "pilot_id": pilot_id,
                        "callsign": callsign,
                        "position": position,
                        # "team_name": team_name,
                        # "node": node,
                        # "heat": heat,
                        "method_label": method_label,
                        # "rank_fields": meta["rank_fields"],
                        # "rank_values": rank_values,  # Qui rimangono solo i valori rimanenti
                    }

                    #print(pilot)

                    rankpayload[pilot_id] = pilot

            db = self._rhapi.db    
            fullresults = db.raceclass_results(class_id)
            if fullresults is not None:
                meta = fullresults["meta"]
                leaderboards = ["by_consecutives", "by_race_time", "by_fastest_lap"]
                for leaderboard in leaderboards:
                    if leaderboard in fullresults:
                        for result in fullresults[leaderboard]:
                            pilot_id = result["pilot_id"]
                            if pilot_id in rankpayload:
                                rankpayload[pilot_id]["consecutives"] = result["consecutives"]
                                rankpayload[pilot_id]["fastest_lap"] = result["fastest_lap"]
                                rankpayload[pilot_id]["fastest_lap_raw"] = result["fastest_lap_raw"]
                            else:
                                rank_values = result.copy()

                                pilot_id = rank_values.pop("pilot_id", None)
                                callsign = rank_values.pop("callsign", None)
                                position = rank_values.pop("position", None)
                                # team_name = rank_values.pop("team_name", None)
                                # node = rank_values.pop("node", None)
                                # total_time_laps = rank_values.pop("total_time_laps", None)
                                # heat = rank_values.pop("heat", None)
                                consecutives = rank_values.pop("consecutives", None)
                                fastest_lap = rank_values.pop("fastest_lap", None)
                                fastest_lap_raw = rank_values.pop("fastest_lap_raw", None)

                                pilot = {
                                    "classid": class_id,
                                    "classname": raceclass.name,
                                    "pilot_id": pilot_id,
                                    "callsign": callsign,
                                    "position": position,
                                    # "team_name": team_name,
                                    # "node": node,
                                    # "heat": heat,
                                    "consecutives": consecutives,
                                    "fastest_lap": fastest_lap,
                                    "fastest_lap_raw": fastest_lap_raw,
                                    # "rank_fields": meta["rank_fields"],
                                    # "rank_values": rank_values,  # Qui rimangono solo i valori rimanenti
                                }

                                #print(pilot)

                                rankpayload[pilot_id] = pilot
                                
        return rankpayload

    def exportFinalLeaderboard(self, args):
        rhapi = self._rhapi
        keys = self.getEventUUID()

        qualifier_class_id = self._rhapi.db.option('qualifier_class')
        final_class_id = self._rhapi.db.option('final_class')
        small_final_class_id = self._rhapi.db.option('small_final_class')

        SMALL_FINALS_ENABLED = (self._rhapi.db.option("csi_small_final") == "1")

        qualifier_leaderboard = self.generate_results_for_class(qualifier_class_id)
        final_class_leaderboard = self.generate_results_for_class(final_class_id)
        if SMALL_FINALS_ENABLED:
            small_final_class_leaderboard = self.generate_results_for_class(small_final_class_id)
        else:
            small_final_class_leaderboard = dict()

        """
        print("QUALIFICHE")
        for elem in qualifier_leaderboard:
            print(f"'{elem}':")
            print(json.dumps(qualifier_leaderboard[elem], indent=2))

        print("FINALI")
        for elem in final_class_leaderboard:
            print(f"'{elem}':")
            print(json.dumps(final_class_leaderboard[elem], indent=2))

        print("FINALINE")
        for elem in small_final_class_leaderboard:
            print(f"'{elem}':")
            print(json.dumps(small_final_class_leaderboard[elem], indent=2))
        """

        # Ordinamento dei piloti nella leaderboard finale:
        # - Dal 1° al 16° posto si prendono i risultati delle finali
        # - Dal 17° posto in poi si prendono i piloti dal 3° posto in poi delle finaline
        # - Se le finaline non si fanno, allora si prendono i piloti dal 17° posto in poi dalle qualifiche

        # Per ogni pilota mi servono questi dati:
        # - pilot_id: ID del pilota
        # - callsign: nome del pilota
        # - position: posizione finale in classifica
        # - qualifier_position: posizione in qualifica
        # - tq: True se è il pilota con il TQ
        # - consecutives: tempo in qualifica su 3 giri
        # - fastest_lap: miglior tempo sul giro considerando qualifica, finali e finaline
        # - the_fastest: True se è il pilota che ha fatto il miglior tempo sul giro

        def sort_leaderboard(leaderboard):
            # In general, leaderboards are already sorted by position, but sort them explicitly to be sure.
            # However consider that the "position" field could be missing for some pilots (for example if they do not complete any laps),
            # handle this case by putting them at the end of the leaderboard.
            leaderboard = list(leaderboard.values())
            leaderboard_with_position = [x for x in leaderboard if x.get("position") is not None]
            leaderboard_without_position = [x for x in leaderboard if x.get("position") is None]
            for i, element in enumerate(leaderboard_without_position):
                if not element.get("position"):
                    element["position"] = len(leaderboard_with_position)+i+1
            leaderboard_sorted = sorted(leaderboard_with_position, key=lambda x: x['position']) + leaderboard_without_position
            return leaderboard_sorted

        qualifier_leaderboard_sorted = sort_leaderboard(qualifier_leaderboard)
        final_class_leaderboard_sorted = sort_leaderboard(final_class_leaderboard)
        small_final_class_leaderboard_sorted = sort_leaderboard(small_final_class_leaderboard)

        position = 1
        the_fastest_lap = float('+inf')
        if SMALL_FINALS_ENABLED:
            final_leaderboard = final_class_leaderboard_sorted[:16] + small_final_class_leaderboard_sorted[2:]
        else:
            final_leaderboard = final_class_leaderboard_sorted[:16] + qualifier_leaderboard_sorted[16:]

        for element in final_leaderboard:
            element["position"] = position
            element["the_fastest"] = 0
            for qualifier_element in qualifier_leaderboard_sorted:
                if qualifier_element["pilot_id"] == element["pilot_id"]:
                    element["qualifier_position"] = qualifier_element["position"]
                    element["tq"] = 1 if (qualifier_element["position"] == 1) else 0
                    element["consecutives"] = qualifier_element["consecutives"] if qualifier_element["consecutives"] else rhapi.utils.format_time_to_str(0)
                    if element["fastest_lap_raw"] == 0:
                        element["fastest_lap_raw"] = qualifier_element["fastest_lap_raw"]
                    if element["fastest_lap_raw"] != 0 and qualifier_element["fastest_lap_raw"] != 0:
                        element["fastest_lap_raw"] = min(element["fastest_lap_raw"], qualifier_element["fastest_lap_raw"])
                    if element["fastest_lap_raw"] != 0:
                        the_fastest_lap = min(the_fastest_lap, element["fastest_lap_raw"])
            if SMALL_FINALS_ENABLED:
                for small_final_element in small_final_class_leaderboard_sorted:
                    if small_final_element["pilot_id"] == element["pilot_id"]:
                        if element["fastest_lap_raw"] == 0:
                            element["fastest_lap_raw"] = small_final_element["fastest_lap_raw"]
                        if element["fastest_lap_raw"] != 0 and small_final_element["fastest_lap_raw"] != 0:
                            element["fastest_lap_raw"] = min(element["fastest_lap_raw"], small_final_element["fastest_lap_raw"])
                        if element["fastest_lap_raw"] != 0:
                            the_fastest_lap = min(the_fastest_lap, element["fastest_lap_raw"])
            # get printable time
            element["fastest_lap"] = rhapi.utils.format_time_to_str(element["fastest_lap_raw"])
            position += 1

        for element in final_leaderboard:
            if element["fastest_lap_raw"] == the_fastest_lap:
                element["the_fastest"] = 1
                break

        """
        position = 1
        for elem in final_leaderboard:
            print(f"'{position}':")
            print(json.dumps(elem, indent=2))
            position += 1
        """
        
        return final_leaderboard

    def laptime_listener(self, args):
        rhapi = self._rhapi
        keys = self.getEventUUID()

        if self.isConnected() and self.isEnabled() and keys["notempty"]:

            raceid = args["race_id"]

            savedracemeta = self._rhapi.db.race_by_id(raceid)
            classid = savedracemeta.class_id
            heatid = savedracemeta.heat_id
            roundid = savedracemeta.round_id

            raceclass = self._rhapi.db.raceclass_by_id(classid)
            classname = raceclass.name

            raceresults = self._rhapi.db.race_results(raceid)
            primary_leaderboard = raceresults["meta"]["primary_leaderboard"]
            filteredraceresults = raceresults[primary_leaderboard]

            pilotruns = self._rhapi.db.pilotruns_by_race(raceid)

            pilotlaps = []
            for run in pilotruns:
                runid = run.id
                laps = self._rhapi.db.laps_by_pilotrun(runid)
                for lap in laps:

                    if lap.deleted == False:
                        thislap = {
                            "id": lap.id,
                            "race_id": lap.race_id,
                            "pilotrace_id": lap.pilotrace_id,
                            "pilot_id": lap.pilot_id,
                            "lap_time_stamp": lap.lap_time_stamp,
                            "lap_time": lap.lap_time,
                            "lap_time_formatted": lap.lap_time_formatted,
                            "deleted": 1 if lap.deleted else 0,
                            "node_index": lap.node_index
                        }
                        pilotlaps.append(thislap)

            payload = {
                "event_uuid": keys["event_uuid"],
                "raceid": raceid,
                "classid": classid,
                "classname": classname,
                "heatid": heatid,
                "roundid": roundid,
                "method_label": primary_leaderboard,
                "roundresults": filteredraceresults,
                "pilotlaps": pilotlaps
            }

            x = requests.post(self.CSI_API_ENDPOINT+"/rh/"+self.CSI_API_VERSION+"/?action=laptimes_update", json = payload)
            #print(x.text)
            self.UI_Message(rhapi, x.text)
            self.logger.info("Laps sent to cloud")

    # bozza di funzione per ottenere i risultati delle heat per ranking o per fastest lap, top consecutive ecc...
    def results_listener(self, args):
        
        rhapi = self._rhapi
        keys = self.getEventUUID()

        self.laptime_listener(args)
        savedracemeta = self._rhapi.db.race_by_id(args["race_id"])
        classid = savedracemeta.class_id
  
        raceclass = self._rhapi.db.raceclass_by_id(classid)
        classname = raceclass.name
        ranking = raceclass.ranking
        if self.isConnected() and self.isEnabled() and keys["notempty"]:

            rankpayload = []
            resultpayload = []

            if ranking != None:
                if isinstance(ranking, bool) and ranking is False:
                    rankpayload = []
                else:
                    meta = ranking["meta"]
                    method_label = meta["method_label"]
                    ranks = ranking["ranking"]

                    for rank in ranks:
                        # Specifieke waardes ophalen en verwijderen uit rank
                        rank_values = rank.copy()  # Maak een kopie om originele data niet te overschrijven

                        pilot_id = rank_values.pop("pilot_id", None)
                        callsign = rank_values.pop("callsign", None)
                        position = rank_values.pop("position", None)
                        team_name = rank_values.pop("team_name", None)
                        node = rank_values.pop("node", None)
                        total_time_laps = rank_values.pop("total_time_laps", None)

                        # heat = rank_values.pop("heat", None)  # Uncomment als 'heat' wordt gebruikt

                        # Maak het pilot-dict
                        pilot = {
                            "classid": classid,
                            "classname": classname,
                            "pilot_id": pilot_id,
                            "callsign": callsign,
                            "position": position,
                            "team_name": team_name,
                            "node": node,
                            # "heat": heat,  # Uncomment als 'heat' wordt gebruikt
                            "method_label": method_label,
                            "rank_fields": meta["rank_fields"],
                            "rank_values": rank_values,  # Hier blijven alleen de overgebleven waardes over
                        }

                        # Debug output (indien nodig)
                        print(pilot)

                        # Toevoegen aan rankpayload
                        rankpayload.append(pilot)    

            db = self._rhapi.db    
            fullresults = db.raceclass_results(classid)
            if fullresults is not None:
                meta = fullresults["meta"]
                leaderboards = ["by_consecutives", "by_race_time", "by_fastest_lap"]

                for leaderboard in leaderboards:
                    if leaderboard in fullresults:
                        for result in fullresults[leaderboard]:
                            pilot = {
                                "classid": classid,
                                "classname": classname,
                                "pilot_id": result["pilot_id"],
                                "callsign": result["callsign"],
                                "team": result["team_name"],
                                "node": result["node"],
                                "points": '',
                                "position": result["position"],
                                "consecutives": result["consecutives"],
                                "consecutives_base": result["consecutives_base"],
                                "laps": result["laps"],
                                "starts": result["starts"],
                                "total_time": result["total_time"],
                                "total_time_laps": result["total_time_laps"],
                                "last_lap": result["last_lap"],
                                "last_lap_raw": result["last_lap_raw"],
                                "average_lap": result["average_lap"],
                                "fastest_lap": result["fastest_lap"],
                                "fastest_lap_source_round": (result.get("fastest_lap_source") or {}).get("round", ''),
                                "consecutives_source_round": (result.get("consecutives_source") or {}).get("round", ''),
                                "total_time_raw": result["total_time_raw"],
                                "total_time_laps_raw": result["total_time_laps_raw"],
                                "average_lap_raw": result["average_lap_raw"],
                                "fastest_lap_source_heat": (result.get("fastest_lap_source") or {}).get("heat", ''),
                                "fastest_lap_source_displayname": (result.get("fastest_lap_source") or {}).get("displayname", ''),
                                "consecutives_source_heat": (result.get("consecutives_source") or {}).get("heat", ''),
                                "consecutives_source_displayname": (result.get("consecutives_source") or {}).get("displayname", ''),
                                "consecutives_lap_start": result.get("consecutive_lap_start", ''),
                                "method_label": leaderboard  # Noteer welk leaderboard gebruikt is
                            }
                            resultpayload.append(pilot)

                payload = {
                    "event_uuid": keys["event_uuid"],
                    "ranking": rankpayload,
                    "results": resultpayload,
                    "classid": classid
                }
                x = requests.post(self.CSI_API_ENDPOINT+"/rh/"+self.CSI_API_VERSION+"/?action=leaderboard_update", json = payload)
                print(x.text)
                self.UI_Message(rhapi, x.text)

                self.logger.info("Results sent to cloud")
            else:
                self.logger.info("No results available to resync")
        else:
            self.logger.warning("No internet connection available")

    def register_handlers(self, args):
        """
        Register export handlers

        :param args: Default callback arguments
        """

        def write_csv(data):
            output = io.StringIO()
            output.write('"Pos Qual";"Pos";"Cognome Nome";"Pole";"Best lap Qual";"Best lap Gara";"Best Lap"\n')
            for row in data:
                output.write(f'"{row["qualifier_position"]}";"{row["position"]}";"{row["callsign"]}";"{row["tq"]}";"{row["consecutives"]}";"{row["fastest_lap"]}";"{row["the_fastest"]}"\n')

            return {
                'data': output.getvalue(),
                'encoding': 'text/csv',
                'ext': 'csv'
            }

        def write_json(data):
            output = json.dumps(data, indent='\t')

            return {
                'data': output,
                'encoding': 'application/json',
                'ext': 'json'
            }

        def assemble_csi_upload(rhapi):
            """
            payload = {}
            payload["import_settings"] = "upload_FPVScores"
            payload["Pilot"] = _assemble_pilots_complete(rhapi)
            payload["Heat"] = rhapi.db.heats
            payload["HeatNode"] = _assemble_heatnodes_complete(rhapi)
            payload["RaceClass"] = rhapi.db.raceclasses
            payload["GlobalSettings"] = rhapi.db.options
            payload["FPVScores_results"] = rhapi.eventresults.results

            return payload
            """
            return self.exportFinalLeaderboard(args)

        #if "register_fn" in args:
        #    args["register_fn"](
        #        DataExporter(
        #            "JSON CSI Upload",
        #            write_json,
        #            assemble_csi_upload,
        #        )
        #    )
        
        if "register_fn" in args:
            args["register_fn"](
                DataExporter(
                    "CSV CSI Upload",
                    write_csv,
                    assemble_csi_upload,
                )
            )
