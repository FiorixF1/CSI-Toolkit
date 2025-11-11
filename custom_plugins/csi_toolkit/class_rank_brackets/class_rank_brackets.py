''' Class ranking method: Brackets '''

import logging
import RHUtils
from eventmanager import Evt
from RHRace import StartBehavior
from Results import RaceClassRankMethod
from RHUI import UIField, UIFieldType, UIFieldSelectOption

logger = logging.getLogger(__name__)



# References for 2025
# MultiGP doc link: https://docs.google.com/document/d/1U4aL9TgKGdlz1y04VMlKoSLFip_msUySuRq6ZnWwh7k/edit?tab=t.0#heading=h.yystmlsjl1ei
# FAI doc link: https://www.fai.org/sites/default/files/ciam/wcup_drones/sc4_vol_f9_dronesport_25_1.pdf



# Constants
MULTIGP = "MultiGP"
FAI = "FAI"
CSI = "CSI Drone Racing"



def apply_tiebreaker(leaderboard, qualifier, first_position, second_position):
    # assume that first_position < second_position and they are 1-based
    from_index = first_position-1
    to_index = second_position

    # extract the set of pilots from the leaderboard
    leaderboard_slice = leaderboard[from_index:to_index]

    # order them by position in qualifier class
    leaderboard_slice = sorted(leaderboard_slice, key=lambda x: qualifier.index(x['pilot_id']) if x else 1024) # corner case for missing pilots

    for i in range(to_index-from_index):
        # update the order of pilots in the leaderboard
        leaderboard[from_index+i] = leaderboard_slice[i]
        # and their position
        if leaderboard[from_index+i]:
            # corner case for missing pilots
            leaderboard[from_index+i]['position'] = first_position+i



def apply_tiebreaker_generic(leaderboard, qualifier, number_of_heats, bracket_type):
    if bracket_type == MULTIGP or bracket_type == CSI:
        # no tiebreaker for ddr8de
        if number_of_heats == 14:
            # multigp16
            apply_tiebreaker(leaderboard, qualifier, 9, 10)    # Q1
            apply_tiebreaker(leaderboard, qualifier, 11, 12)   # Q2
            apply_tiebreaker(leaderboard, qualifier, 13, 14)   # Q3
            apply_tiebreaker(leaderboard, qualifier, 15, 16)   # Q4
    elif bracket_type == FAI:
        if number_of_heats == 6:
            # ddr8de
            apply_tiebreaker(leaderboard, qualifier, 5, 6)     # Q1
            apply_tiebreaker(leaderboard, qualifier, 7, 8)     # Q2
        elif number_of_heats == 8:
            # fai16
            apply_tiebreaker(leaderboard, qualifier, 9,  16)   # Q1
        elif number_of_heats == 14:
            # fai16de
            apply_tiebreaker(leaderboard, qualifier, 9,  12)   # Q1
            apply_tiebreaker(leaderboard, qualifier, 13, 16)   # Q2
        elif number_of_heats == 16:
            # fai32
            apply_tiebreaker(leaderboard, qualifier, 9,  16)   # Q1
            apply_tiebreaker(leaderboard, qualifier, 17, 32)   # Q2
        elif number_of_heats == 30:
            # fai32de
            apply_tiebreaker(leaderboard, qualifier, 9,  12)   # Q1
            apply_tiebreaker(leaderboard, qualifier, 13, 16)   # Q2
            apply_tiebreaker(leaderboard, qualifier, 17, 24)   # Q3
            apply_tiebreaker(leaderboard, qualifier, 25, 32)   # Q4
        elif number_of_heats == 32:
            # fai64
            apply_tiebreaker(leaderboard, qualifier, 9,  16)   # Q1
            apply_tiebreaker(leaderboard, qualifier, 17, 32)   # Q2
            apply_tiebreaker(leaderboard, qualifier, 33, 64)   # Q3
        elif number_of_heats == 62:
            # fai64de
            apply_tiebreaker(leaderboard, qualifier, 9,  12)   # Q1
            apply_tiebreaker(leaderboard, qualifier, 13, 16)   # Q2
            apply_tiebreaker(leaderboard, qualifier, 17, 24)   # Q3
            apply_tiebreaker(leaderboard, qualifier, 25, 32)   # Q4
            apply_tiebreaker(leaderboard, qualifier, 33, 48)   # Q5
            apply_tiebreaker(leaderboard, qualifier, 49, 64)   # Q6



def build_leaderboard_object_basic(rhapi, position, slot, result):
    return {
        'pilot_id': slot['pilot_id'],
        'callsign': slot['callsign'],
        'team_name': slot['team_name'],
        'position': position,
        'result': result
    }



def build_leaderboard_object(rhapi, position, heats, heat_number, heat_position, result):
    if heat_number <= len(heats):
        heat = heats[heat_number-1]
        # for robustness, don't use heat_results but get results from Round 1 instead
        races = rhapi.db.races_by_heat(heat.id)
        if races:
            race_result = rhapi.db.race_results(races[0])
            if race_result:
                heat_leaderboard = race_result[race_result['meta']['primary_leaderboard']]
                # corner case for heats with missing pilots
                if heat_position <= len(heat_leaderboard):
                    slot = heat_leaderboard[heat_position-1]

                    return {
                        'pilot_id': slot['pilot_id'],
                        'callsign': slot['callsign'],
                        'team_name': slot['team_name'],
                        'position': position,
                        'result': result
                    }

    return None



def build_leaderboard_generic(rhapi, heats, bracket_type):
    logger.info(f"Found {len(heats)} heats in the bracket class")
    if bracket_type == MULTIGP or bracket_type == CSI:
        if len(heats) == 6:
            # ddr8de
            logger.info(f"Format detected: DDR 8 pilots double elimination (MultiGP style)")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 5, 3, "3° in Heat 5"),
                build_leaderboard_object(rhapi, 6,  heats, 5, 4, "4° in Heat 5"),
                build_leaderboard_object(rhapi, 7,  heats, 3, 3, "3° in Heat 3"),
                build_leaderboard_object(rhapi, 8,  heats, 3, 4, "4° in Heat 3")
            ]
        elif len(heats) == 14:
            # multigp16
            logger.info(f"Format detected: MultiGP 16 pilots double elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 13, 3, "3° in Heat 13"),
                build_leaderboard_object(rhapi, 6,  heats, 13, 4, "4° in Heat 13"),
                build_leaderboard_object(rhapi, 7,  heats, 12, 3, "3° in Heat 12"),
                build_leaderboard_object(rhapi, 8,  heats, 12, 4, "4° in Heat 12"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 9,  3, "3° in Heat 9"),   # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 10, 3, "3° in Heat 10"),  # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 11, heats, 9,  4, "4° in Heat 9"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 12, heats, 10, 4, "4° in Heat 10"),  # to be fixed Q2
                ####################################################################################################
                build_leaderboard_object(rhapi, 13, heats, 5,  3, "3° in Heat 5"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 14, heats, 7,  3, "3° in Heat 7"),   # to be fixed Q3
                ####################################################################################################
                build_leaderboard_object(rhapi, 15, heats, 5,  4, "4° in Heat 5"),   # to be fixed Q4
                build_leaderboard_object(rhapi, 16, heats, 7,  4, "4° in Heat 7")    # to be fixed Q4
            ]
        else:
            # unsupported format
            return None
    elif bracket_type == FAI:
        if len(heats) == 6:
            # ddr8de
            logger.info(f"Format detected: DDR 8 pilots double elimination (FAI style)")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                ####################################################################################################
                build_leaderboard_object(rhapi, 5,  heats, 5, 3, "3° in Heat 5"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 6,  heats, 5, 4, "4° in Heat 5"),  # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 7,  heats, 3, 3, "3° in Heat 3"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 8,  heats, 3, 4, "4° in Heat 3")   # to be fixed Q2
            ]
        elif len(heats) == 8:
            # fai16
            logger.info(f"Format detected: FAI 16 pilots single elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 7, 1, "1° in Small Final"),
                build_leaderboard_object(rhapi, 6,  heats, 7, 2, "2° in Small Final"),
                build_leaderboard_object(rhapi, 7,  heats, 7, 3, "3° in Small Final"),
                build_leaderboard_object(rhapi, 8,  heats, 7, 4, "4° in Small Final"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 4, 3, "3° in Heat 4"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 4, 4, "4° in Heat 4"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 3, 3, "3° in Heat 3"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 3, 4, "4° in Heat 3"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 13, heats, 2, 3, "3° in Heat 2"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 14, heats, 2, 4, "4° in Heat 2"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 15, heats, 1, 3, "3° in Heat 1"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 16, heats, 1, 4, "4° in Heat 1")   # to be fixed Q1
            ]
        elif len(heats) == 14:
            # fai16de
            logger.info(f"Format detected: FAI 16 pilots double elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 13, 3, "3° in Heat 13"),
                build_leaderboard_object(rhapi, 6,  heats, 13, 4, "4° in Heat 13"),
                build_leaderboard_object(rhapi, 7,  heats, 11, 3, "3° in Heat 11"),
                build_leaderboard_object(rhapi, 8,  heats, 11, 4, "4° in Heat 11"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 10, 3, "3° in Heat 10"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 10, 4, "4° in Heat 10"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 9,  3, "3° in Heat 9"),   # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 9,  4, "4° in Heat 9"),   # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 13, heats, 6,  3, "3° in Heat 6"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 14, heats, 6,  4, "4° in Heat 6"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 15, heats, 5,  3, "3° in Heat 5"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 16, heats, 5,  4, "4° in Heat 5")    # to be fixed Q2
            ]
        elif len(heats) == 16:
            # fai32
            logger.info(f"Format detected: FAI 32 pilots single elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 15, 1, "1° in Small Final"),
                build_leaderboard_object(rhapi, 6,  heats, 15, 2, "2° in Small Final"),
                build_leaderboard_object(rhapi, 7,  heats, 15, 3, "3° in Small Final"),
                build_leaderboard_object(rhapi, 8,  heats, 15, 4, "4° in Small Final"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 12, 3, "3° in Heat 12"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 12, 4, "4° in Heat 12"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 11, 3, "3° in Heat 11"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 11, 4, "4° in Heat 11"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 13, heats, 10, 3, "3° in Heat 10"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 14, heats, 10, 4, "4° in Heat 10"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 15, heats, 9,  3, "3° in Heat 9"),   # to be fixed Q1
                build_leaderboard_object(rhapi, 16, heats, 9,  4, "4° in Heat 9"),   # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 17, heats, 8,  3, "3° in Heat 8"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 18, heats, 8,  4, "4° in Heat 8"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 19, heats, 7,  3, "3° in Heat 7"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 20, heats, 7,  4, "4° in Heat 7"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 21, heats, 6,  3, "3° in Heat 6"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 22, heats, 6,  4, "4° in Heat 6"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 23, heats, 5,  3, "3° in Heat 5"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 24, heats, 5,  4, "4° in Heat 5"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 25, heats, 4,  3, "3° in Heat 4"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 26, heats, 4,  4, "4° in Heat 4"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 27, heats, 3,  3, "3° in Heat 3"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 28, heats, 3,  4, "4° in Heat 3"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 29, heats, 2,  3, "3° in Heat 2"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 30, heats, 2,  4, "4° in Heat 2"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 31, heats, 1,  3, "3° in Heat 1"),   # to be fixed Q2
                build_leaderboard_object(rhapi, 32, heats, 1,  4, "4° in Heat 1")    # to be fixed Q2
            ]
        elif len(heats) == 30:
            # fai32de
            logger.info(f"Format detected: FAI 32 pilots double elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 29, 3, "3° in Heat 29"),
                build_leaderboard_object(rhapi, 6,  heats, 29, 4, "4° in Heat 29"),
                build_leaderboard_object(rhapi, 7,  heats, 27, 3, "3° in Heat 27"),
                build_leaderboard_object(rhapi, 8,  heats, 27, 4, "4° in Heat 27"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 26, 3, "3° in Heat 26"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 26, 4, "4° in Heat 26"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 25, 3, "3° in Heat 25"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 25, 4, "4° in Heat 25"),  # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 13, heats, 22, 3, "3° in Heat 22"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 14, heats, 22, 4, "4° in Heat 22"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 15, heats, 21, 3, "3° in Heat 21"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 16, heats, 21, 4, "4° in Heat 21"),  # to be fixed Q2
                ####################################################################################################
                build_leaderboard_object(rhapi, 17, heats, 20, 3, "3° in Heat 20"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 18, heats, 20, 4, "4° in Heat 20"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 19, heats, 19, 3, "3° in Heat 19"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 20, heats, 19, 4, "4° in Heat 19"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 21, heats, 18, 3, "3° in Heat 18"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 22, heats, 18, 4, "4° in Heat 18"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 23, heats, 17, 3, "3° in Heat 17"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 24, heats, 17, 4, "4° in Heat 17"),  # to be fixed Q3
                ####################################################################################################
                build_leaderboard_object(rhapi, 25, heats, 16, 3, "3° in Heat 16"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 26, heats, 16, 4, "4° in Heat 16"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 27, heats, 15, 3, "3° in Heat 15"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 28, heats, 15, 4, "4° in Heat 15"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 29, heats, 14, 3, "3° in Heat 14"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 30, heats, 14, 4, "4° in Heat 14"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 31, heats, 13, 3, "3° in Heat 13"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 32, heats, 13, 4, "4° in Heat 13")   # to be fixed Q4
            ]
        elif len(heats) == 32:
            # fai64
            logger.info(f"Format detected: FAI 64 pilots single elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 31, 1, "1° in Small Final"),
                build_leaderboard_object(rhapi, 6,  heats, 31, 2, "2° in Small Final"),
                build_leaderboard_object(rhapi, 7,  heats, 31, 3, "3° in Small Final"),
                build_leaderboard_object(rhapi, 8,  heats, 31, 4, "4° in Small Final"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 28, 3, "3° in Heat 28"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 28, 4, "4° in Heat 28"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 27, 3, "3° in Heat 27"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 27, 4, "4° in Heat 27"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 13, heats, 26, 3, "3° in Heat 26"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 14, heats, 26, 4, "4° in Heat 26"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 15, heats, 25, 3, "3° in Heat 25"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 16, heats, 25, 4, "4° in Heat 25"),  # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 17, heats, 24, 3, "3° in Heat 24"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 18, heats, 24, 4, "4° in Heat 24"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 19, heats, 23, 3, "3° in Heat 23"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 20, heats, 23, 4, "4° in Heat 23"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 21, heats, 22, 3, "3° in Heat 22"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 22, heats, 22, 4, "4° in Heat 22"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 23, heats, 21, 3, "3° in Heat 21"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 24, heats, 21, 4, "4° in Heat 21"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 25, heats, 20, 3, "3° in Heat 20"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 26, heats, 20, 4, "4° in Heat 20"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 27, heats, 19, 3, "3° in Heat 19"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 28, heats, 19, 4, "4° in Heat 19"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 29, heats, 18, 3, "3° in Heat 18"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 30, heats, 18, 4, "4° in Heat 18"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 31, heats, 17, 3, "3° in Heat 17"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 32, heats, 17, 4, "4° in Heat 17"),  # to be fixed Q2
                ####################################################################################################
                build_leaderboard_object(rhapi, 33, heats, 16, 3, "3° in Heat 16"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 34, heats, 16, 4, "4° in Heat 16"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 35, heats, 15, 3, "3° in Heat 15"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 36, heats, 15, 4, "4° in Heat 15"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 37, heats, 14, 3, "3° in Heat 14"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 38, heats, 14, 4, "4° in Heat 14"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 39, heats, 13, 3, "3° in Heat 13"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 40, heats, 13, 4, "4° in Heat 13"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 41, heats, 12, 3, "3° in Heat 12"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 42, heats, 12, 4, "4° in Heat 12"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 43, heats, 11, 3, "3° in Heat 11"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 44, heats, 11, 4, "4° in Heat 11"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 45, heats, 10, 3, "3° in Heat 10"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 46, heats, 10, 4, "4° in Heat 10"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 47, heats, 9,  3, "3° in Heat 9"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 48, heats, 9,  4, "4° in Heat 9"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 49, heats, 8,  3, "3° in Heat 8"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 50, heats, 8,  4, "4° in Heat 8"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 51, heats, 7,  3, "3° in Heat 7"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 52, heats, 7,  4, "4° in Heat 7"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 53, heats, 6,  3, "3° in Heat 6"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 54, heats, 6,  4, "4° in Heat 6"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 55, heats, 5,  3, "3° in Heat 5"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 56, heats, 5,  4, "4° in Heat 5"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 57, heats, 4,  3, "3° in Heat 4"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 58, heats, 4,  4, "4° in Heat 4"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 59, heats, 3,  3, "3° in Heat 3"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 60, heats, 3,  4, "4° in Heat 3"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 61, heats, 2,  3, "3° in Heat 2"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 62, heats, 2,  4, "4° in Heat 2"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 63, heats, 1,  3, "3° in Heat 1"),   # to be fixed Q3
                build_leaderboard_object(rhapi, 64, heats, 1,  4, "4° in Heat 1")    # to be fixed Q3
            ]
        elif len(heats) == 62:
            # fai64de
            logger.info(f"Format detected: FAI 64 pilots double elimination")
            return [
                None,  # top 4 positions are handled later due to CTA logic
                None,
                None,
                None,
                build_leaderboard_object(rhapi, 5,  heats, 61, 3, "3° in Heat 61"),
                build_leaderboard_object(rhapi, 6,  heats, 61, 4, "4° in Heat 61"),
                build_leaderboard_object(rhapi, 7,  heats, 59, 3, "3° in Heat 59"),
                build_leaderboard_object(rhapi, 8,  heats, 59, 4, "4° in Heat 59"),
                ####################################################################################################
                build_leaderboard_object(rhapi, 9,  heats, 58, 3, "3° in Heat 58"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 10, heats, 58, 4, "4° in Heat 58"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 11, heats, 57, 3, "3° in Heat 57"),  # to be fixed Q1
                build_leaderboard_object(rhapi, 12, heats, 57, 4, "4° in Heat 57"),  # to be fixed Q1
                ####################################################################################################
                build_leaderboard_object(rhapi, 13, heats, 54, 3, "3° in Heat 54"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 14, heats, 54, 4, "4° in Heat 54"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 15, heats, 53, 3, "3° in Heat 53"),  # to be fixed Q2
                build_leaderboard_object(rhapi, 16, heats, 53, 4, "4° in Heat 53"),  # to be fixed Q2
                ####################################################################################################
                build_leaderboard_object(rhapi, 17, heats, 52, 3, "3° in Heat 52"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 18, heats, 52, 4, "4° in Heat 52"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 19, heats, 51, 3, "3° in Heat 51"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 20, heats, 51, 4, "4° in Heat 51"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 21, heats, 50, 3, "3° in Heat 50"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 22, heats, 50, 4, "4° in Heat 50"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 23, heats, 49, 3, "3° in Heat 49"),  # to be fixed Q3
                build_leaderboard_object(rhapi, 24, heats, 49, 4, "4° in Heat 49"),  # to be fixed Q3
                ####################################################################################################
                build_leaderboard_object(rhapi, 25, heats, 44, 3, "3° in Heat 44"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 26, heats, 44, 4, "4° in Heat 44"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 27, heats, 43, 3, "3° in Heat 43"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 28, heats, 43, 4, "4° in Heat 43"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 29, heats, 42, 3, "3° in Heat 42"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 30, heats, 42, 4, "4° in Heat 42"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 31, heats, 41, 3, "3° in Heat 41"),  # to be fixed Q4
                build_leaderboard_object(rhapi, 32, heats, 41, 4, "4° in Heat 41"),  # to be fixed Q4
                ####################################################################################################
                build_leaderboard_object(rhapi, 33, heats, 40, 3, "3° in Heat 40"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 34, heats, 40, 4, "4° in Heat 40"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 35, heats, 39, 3, "3° in Heat 39"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 36, heats, 39, 4, "4° in Heat 39"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 37, heats, 38, 3, "3° in Heat 38"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 38, heats, 38, 4, "4° in Heat 38"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 39, heats, 37, 3, "3° in Heat 37"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 40, heats, 37, 4, "4° in Heat 37"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 41, heats, 36, 3, "3° in Heat 36"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 42, heats, 36, 4, "4° in Heat 36"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 43, heats, 35, 3, "3° in Heat 35"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 44, heats, 35, 4, "4° in Heat 35"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 45, heats, 34, 3, "3° in Heat 34"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 46, heats, 34, 4, "4° in Heat 34"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 47, heats, 33, 3, "3° in Heat 33"),  # to be fixed Q5
                build_leaderboard_object(rhapi, 48, heats, 33, 4, "4° in Heat 33"),  # to be fixed Q5
                ####################################################################################################
                build_leaderboard_object(rhapi, 49, heats, 32, 3, "3° in Heat 32"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 50, heats, 32, 4, "4° in Heat 32"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 51, heats, 31, 3, "3° in Heat 31"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 52, heats, 31, 4, "4° in Heat 31"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 53, heats, 30, 3, "3° in Heat 30"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 54, heats, 30, 4, "4° in Heat 30"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 55, heats, 29, 3, "3° in Heat 29"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 56, heats, 29, 4, "4° in Heat 29"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 57, heats, 28, 3, "3° in Heat 28"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 58, heats, 28, 4, "4° in Heat 28"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 59, heats, 27, 3, "3° in Heat 27"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 60, heats, 27, 4, "4° in Heat 27"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 61, heats, 26, 3, "3° in Heat 26"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 62, heats, 26, 4, "4° in Heat 26"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 63, heats, 25, 3, "3° in Heat 25"),  # to be fixed Q6
                build_leaderboard_object(rhapi, 64, heats, 25, 4, "4° in Heat 25")   # to be fixed Q6
            ]
        else:
            # unsupported format
            return None
    else:
        # unsupported format
        return None



####################################################################################################

previous_winners_names = dict()
previous_chace_the_ace_winner = dict()
previous_iron_man_winner = dict()

def brackets(rhapi, race_class, args):
    """ look for qualifier results """
    if int(args["qualifier_class"]) == int(race_class.id):
        logger.error(f"Failed building ranking: brackets cannot use themselves as qualifier class")
        return {}, {}

    qualifier_result = None
    for raceclass in rhapi.db.raceclasses:
        if int(raceclass.id) == int(args["qualifier_class"]):
            qualifier_result = rhapi.db.raceclass_results(raceclass)

    if not qualifier_result:
        logger.error(f"Failed building ranking: qualifier result not available")
        return {}, {}

    qualifier = qualifier_result[qualifier_result['meta']['primary_leaderboard']]
    # in general, leaderboards are already sorted by position, but sort them explicitly to be sure
    # however consider that pilots could be without a value for the "position" field (for example if they do not complete any laps),
    # handle this case by putting them at the end of the leaderboard
    qualifier_with_position = [x for x in qualifier if x.get("position") is not None]
    qualifier_without_position = [x for x in qualifier if x.get("position") is None]
    for i, element in enumerate(qualifier_without_position):
        if not element.get("position"):
            element["position"] = len(qualifier_with_position)+i+1
    # sort by position (to be safe) and extract only the pilot IDs
    qualifier = list(map(lambda x: x['pilot_id'], sorted(qualifier_with_position, key=lambda x: x['position']) + qualifier_without_position))
    logger.info(f"Found {len(qualifier)} pilots in the qualifier class")

    """ build leaderboard """
    heats = rhapi.db.heats_by_class(race_class.id)
    NUMBER_OF_HEATS = len(heats)

    try:
        leaderboard = build_leaderboard_generic(rhapi, heats, args["bracket_type"])
    except Exception as e:
        logger.error(f"Failed building ranking: an exception occurred while generating leaderboard ({e})")
        return {}, {}

    if not leaderboard:
        logger.error(f"Failed building ranking: unsupported format (" + args["bracket_type"] + " brackets with " + str(len(heats)) + " heats)")
        return {}, {}

    """ apply qualifier results to resolve ties """
    try:
        apply_tiebreaker_generic(leaderboard, qualifier, NUMBER_OF_HEATS, args["bracket_type"])
    except Exception as e:
        logger.error(f"Failed building ranking: an exception occurred while resolving ties ({e})")
        return {}, {}

    """ apply Chase the Ace and Iron Man rule """
    if 'chase_the_ace' in args and args['chase_the_ace']:
        # verify if Iron Man rule can be applied
        if 'iron_man' in args and args['iron_man']:
            IS_IRON_MAN_AVAILABLE = True
            tq_pilot_id = qualifier[0]

            # verify that the pilot holding the TQ has won all heats before the final
            for heat in heats[:-1]:
                # for robustness, don't use heat_results but get results from Round 1 instead
                races = rhapi.db.races_by_heat(heat.id)
                if races:
                    race_result = rhapi.db.race_results(races[0])
                    if race_result:
                        heat_leaderboard = race_result[race_result['meta']['primary_leaderboard']]
                        pilot_ids = list(map(lambda x: x['pilot_id'], heat_leaderboard))
                        winner_pilot_id = heat_leaderboard[0]['pilot_id']
                        if tq_pilot_id in pilot_ids and winner_pilot_id != tq_pilot_id:
                            IS_IRON_MAN_AVAILABLE = False
                            break
        else:
            IS_IRON_MAN_AVAILABLE = False

        # initialize data for each pilot in the final
        slots = rhapi.db.slots_by_heat(heats[-1].id)
        winners = {}
        for slot in slots:
            pilot_id = slot.pilot_id
            winners[pilot_id] = {
                "wins": 0,
                "points": 0,
                "big_points": 0
            }

        winners_names = []
        RACE_IS_OVER = False

        # extract rounds from the final
        races = rhapi.db.races_by_heat(heats[-1].id)
        for race_number, race in enumerate(races):
            race_result = rhapi.db.race_results(race)

            if race_result:
                heat_leaderboard = race_result[race_result['meta']['primary_leaderboard']]
                winner_pilot_id = heat_leaderboard[0]['pilot_id']

                if race_number == 0 and IS_IRON_MAN_AVAILABLE and winner_pilot_id == tq_pilot_id:
                    # race is over (Iron Man)
                    leaderboard[0] = build_leaderboard_object(rhapi, 1, heats, NUMBER_OF_HEATS, 1, "CTA [1] [1]")
                    leaderboard[1] = build_leaderboard_object(rhapi, 2, heats, NUMBER_OF_HEATS, 2, "[2] [2]")
                    leaderboard[2] = build_leaderboard_object(rhapi, 3, heats, NUMBER_OF_HEATS, 3, "[3] [3]")
                    leaderboard[3] = build_leaderboard_object(rhapi, 4, heats, NUMBER_OF_HEATS, 4, "[4] [4]")

                    RACE_IS_OVER = True

                    prev = previous_iron_man_winner.get(race_class.id)
                    curr = leaderboard[0]['callsign']
                    if prev != curr:
                        rhapi.ui.message_alert(rhapi.__('Iron Man Winner: {}').format(curr))
                        previous_iron_man_winner[race_class.id] = curr

                    break

                winners[winner_pilot_id]["wins"] += 1
                winners_names.append(rhapi.db.pilot_by_id(winner_pilot_id).display_callsign)

                winners[heat_leaderboard[0]['pilot_id']]["points"] += 1
                winners[heat_leaderboard[1]['pilot_id']]["points"] += 2
                winners[heat_leaderboard[2]['pilot_id']]["points"] += 3
                winners[heat_leaderboard[3]['pilot_id']]["points"] += 4

                winners[heat_leaderboard[0]['pilot_id']]["big_points"] += 1000
                winners[heat_leaderboard[1]['pilot_id']]["big_points"] += 100
                winners[heat_leaderboard[2]['pilot_id']]["big_points"] += 10
                winners[heat_leaderboard[3]['pilot_id']]["big_points"] += 1

                RACE_IS_OVER = False
                for pilot_id in winners:
                    if winners[pilot_id]["wins"] > 1:
                        # race is over (Chase the Ace)
                        RACE_IS_OVER = True
                        break
                if RACE_IS_OVER:
                    if args["bracket_type"] != CSI:
                        # positions from second to fourth are point based
                        # in case of a tie, the result of the latest heat is considered
                        # the smartest way to implement this is take the leaderboard of the last heat and order it by points using Bubblesort as sorting algorithm
                        # it makes sense because Bubblesort does not alter the order of items that are equal 
                        # and it is efficient since we have to order only three elements :)
                        if winners[heat_leaderboard[1]['pilot_id']]["points"] > winners[heat_leaderboard[2]['pilot_id']]["points"]:
                            heat_leaderboard[1], heat_leaderboard[2] = heat_leaderboard[2], heat_leaderboard[1]
                        if winners[heat_leaderboard[2]['pilot_id']]["points"] > winners[heat_leaderboard[3]['pilot_id']]["points"]:
                            heat_leaderboard[2], heat_leaderboard[3] = heat_leaderboard[3], heat_leaderboard[2]
                        if winners[heat_leaderboard[1]['pilot_id']]["points"] > winners[heat_leaderboard[2]['pilot_id']]["points"]:
                            heat_leaderboard[1], heat_leaderboard[2] = heat_leaderboard[2], heat_leaderboard[1]
                        if winners[heat_leaderboard[2]['pilot_id']]["points"] > winners[heat_leaderboard[3]['pilot_id']]["points"]:
                            heat_leaderboard[2], heat_leaderboard[3] = heat_leaderboard[3], heat_leaderboard[2]
                        # build top-4 leaderboard
                        leaderboard[0] = build_leaderboard_object_basic(rhapi, 1, heat_leaderboard[0], f"CTA [{winners[heat_leaderboard[0]['pilot_id']]['points']}] [1]")
                        leaderboard[1] = build_leaderboard_object_basic(rhapi, 2, heat_leaderboard[1], f"[{winners[heat_leaderboard[1]['pilot_id']]['points']}] [2]")
                        leaderboard[2] = build_leaderboard_object_basic(rhapi, 3, heat_leaderboard[2], f"[{winners[heat_leaderboard[2]['pilot_id']]['points']}] [3]")
                        leaderboard[3] = build_leaderboard_object_basic(rhapi, 4, heat_leaderboard[3], f"[{winners[heat_leaderboard[3]['pilot_id']]['points']}] [4]")
                    else:
                        # CSI ranking is similar to MultiGP/FAI, but points are different and, in case of a tie, qualifier class is used as tiebreaker
                        if winners[heat_leaderboard[1]['pilot_id']]["big_points"] < winners[heat_leaderboard[2]['pilot_id']]["big_points"]:
                            heat_leaderboard[1], heat_leaderboard[2] = heat_leaderboard[2], heat_leaderboard[1]
                        if winners[heat_leaderboard[2]['pilot_id']]["big_points"] < winners[heat_leaderboard[3]['pilot_id']]["big_points"]:
                            heat_leaderboard[2], heat_leaderboard[3] = heat_leaderboard[3], heat_leaderboard[2]
                        if winners[heat_leaderboard[1]['pilot_id']]["big_points"] < winners[heat_leaderboard[2]['pilot_id']]["big_points"]:
                            heat_leaderboard[1], heat_leaderboard[2] = heat_leaderboard[2], heat_leaderboard[1]
                        if winners[heat_leaderboard[2]['pilot_id']]["big_points"] < winners[heat_leaderboard[3]['pilot_id']]["big_points"]:
                            heat_leaderboard[2], heat_leaderboard[3] = heat_leaderboard[3], heat_leaderboard[2]
                        # build temporary top-4 leaderboard (ties have not been solved yet)
                        leaderboard[0] = build_leaderboard_object_basic(rhapi, 1, heat_leaderboard[0], "")
                        leaderboard[1] = build_leaderboard_object_basic(rhapi, 2, heat_leaderboard[1], "")
                        leaderboard[2] = build_leaderboard_object_basic(rhapi, 3, heat_leaderboard[2], "")
                        leaderboard[3] = build_leaderboard_object_basic(rhapi, 4, heat_leaderboard[3], "")
                        # look for ties and solve them
                        if winners[heat_leaderboard[1]['pilot_id']]["big_points"] == winners[heat_leaderboard[2]['pilot_id']]["big_points"] and \
                           winners[heat_leaderboard[1]['pilot_id']]["big_points"] == winners[heat_leaderboard[3]['pilot_id']]["big_points"]:
                            apply_tiebreaker(leaderboard, qualifier, 2, 4)
                        elif winners[heat_leaderboard[1]['pilot_id']]["big_points"] == winners[heat_leaderboard[2]['pilot_id']]["big_points"]:
                            apply_tiebreaker(leaderboard, qualifier, 2, 3)
                        elif winners[heat_leaderboard[2]['pilot_id']]["big_points"] == winners[heat_leaderboard[3]['pilot_id']]["big_points"]:
                            apply_tiebreaker(leaderboard, qualifier, 3, 4)
                        # update top-4 leaderboard
                        leaderboard[0]["result"] = "CTA [1] [1]"
                        leaderboard[1]["result"] = "[2] [2]"
                        leaderboard[2]["result"] = "[3] [3]"
                        leaderboard[3]["result"] = "[4] [4]"

                    prev = previous_chace_the_ace_winner.get(race_class.id)
                    curr = leaderboard[0]['callsign']
                    if prev != curr:
                        rhapi.ui.message_alert(rhapi.__('Chase the Ace Winner: {}').format(curr))
                        previous_chace_the_ace_winner[race_class.id] = curr

                    break

        if not RACE_IS_OVER and len(winners_names) > 0:
            prev = previous_winners_names.get(race_class.id)
            curr = ', '.join(winners_names)
            if prev != curr:
                rhapi.ui.message_alert(rhapi.__('Pilots with one win: {}').format(curr))
                previous_winners_names[race_class.id] = curr
    else:
        # if CTA is disabled, just use the results of the last heat
        leaderboard[0] = build_leaderboard_object(rhapi, 1, heats, NUMBER_OF_HEATS, 1, "1° in Final")
        leaderboard[1] = build_leaderboard_object(rhapi, 2, heats, NUMBER_OF_HEATS, 2, "2° in Final")
        leaderboard[2] = build_leaderboard_object(rhapi, 3, heats, NUMBER_OF_HEATS, 3, "3° in Final")
        leaderboard[3] = build_leaderboard_object(rhapi, 4, heats, NUMBER_OF_HEATS, 4, "4° in Final")

    """ remove empty slots """
    leaderboard = list(filter(lambda x: x != None, leaderboard))

    meta = {
        'rank_fields': [{
            'name': 'result',
            'label': 'Result'
        }]
    }

    return leaderboard, meta

####################################################################################################



class_rank_method = None
def register_handlers(rhapi, args):
    global class_rank_method

    classes = rhapi.db.raceclasses
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

    if not class_rank_method:
        class_rank_method = RaceClassRankMethod(
            "Brackets",
            brackets,
            {
                'bracket_type': CSI,
                'qualifier_class': default_class,
                'chase_the_ace': True,
                'iron_man': True,
            },
            [
                UIField('bracket_type',
                    "Bracket type",
                    UIFieldType.SELECT,
                    options=[UIFieldSelectOption(CSI, CSI),
                             UIFieldSelectOption(MULTIGP, MULTIGP),
                             UIFieldSelectOption(FAI, FAI)],
                    value=CSI,
                    desc="Type of brackets"),
                UIField('qualifier_class',
                    "Qualifier class",
                    UIFieldType.SELECT,
                    options=options,
                    value=default_class,
                    desc="Class used in qualification stage"),
                UIField('chase_the_ace',
                    "Chase the Ace",
                    UIFieldType.CHECKBOX,
                    value=True,
                    desc="Apply the Chase the Ace format in the final heat"),
                UIField('iron_man',
                    "Iron Man rule",
                    UIFieldType.CHECKBOX,
                    value=True,
                    desc="Apply the Iron Man rule in the final heat (CTA is required)"),
            ]
        )
        args['register_fn'](class_rank_method)
    else:
        # update class selector if the rank has been already initialized
        class_rank_method.settings[1].options = options

def initialize(rhapi):
    # initialization
    rhapi.events.on(Evt.CLASS_RANK_INITIALIZE, lambda args: register_handlers(rhapi, args))
    # update
    rhapi.events.on(Evt.CLASS_ADD, lambda args: register_handlers(rhapi, args))
    rhapi.events.on(Evt.CLASS_DUPLICATE, lambda args: register_handlers(rhapi, args))
    rhapi.events.on(Evt.CLASS_ALTER, lambda args: register_handlers(rhapi, args))
    rhapi.events.on(Evt.CLASS_DELETE, lambda args: register_handlers(rhapi, args))
