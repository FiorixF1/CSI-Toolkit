''' Heat generator for 8 pilots Double Elimination bracket '''

import logging
import RHUtils
import random
from eventmanager import Evt
from HeatGenerator import HeatGenerator, HeatPlan, HeatPlanSlot, SeedMethod
from RHUI import UIField, UIFieldType, UIFieldSelectOption

logger = logging.getLogger(__name__)


def generate8PilotDEBracketHeats(rhapi, generate_args=None):
    # Parameters ophalen of defaults gebruiken
    race1_qualifiers = generate_args.get('race1_qualifiers', '17,24,20,21')
    race2_qualifiers = generate_args.get('race2_qualifiers', '18,23,19,22')
    heat_names = generate_args.get('heat_names',
        'Race 1 - Winner Bracket,Race 2 - Winner Bracket,Race 3 - Lower Bracket,Race 4 - Winner Bracket,Race 5 - Lower Bracket,Race 6 - Final'
    )
    
    # Omzetten naar lijsten
    race1_qualifiers = [int(x.strip()) for x in race1_qualifiers.split(',')]
    race2_qualifiers = [int(x.strip()) for x in race2_qualifiers.split(',')]
    heat_names = [x.strip() for x in heat_names.split(',')]

    heats = []

    # Race 1
    heat1 = HeatPlan(heat_names[0], [
        HeatPlanSlot(SeedMethod.INPUT, race1_qualifiers[0]),
        HeatPlanSlot(SeedMethod.INPUT, race1_qualifiers[1]),
        HeatPlanSlot(SeedMethod.INPUT, race1_qualifiers[2]),
        HeatPlanSlot(SeedMethod.INPUT, race1_qualifiers[3]),
    ])
    heats.append(heat1)

    # Race 2
    heat2 = HeatPlan(heat_names[1], [
        HeatPlanSlot(SeedMethod.INPUT, race2_qualifiers[0]),
        HeatPlanSlot(SeedMethod.INPUT, race2_qualifiers[1]),
        HeatPlanSlot(SeedMethod.INPUT, race2_qualifiers[2]),
        HeatPlanSlot(SeedMethod.INPUT, race2_qualifiers[3]),
    ])
    heats.append(heat2)

    # Race 3 - Lower Bracket (Race 1 - 3rd, 4th; Race 2 - 3rd, 4th)
    heat3 = HeatPlan(heat_names[2], [
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 3, 0),  # Race 1 - 3rd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 4, 0),  # Race 1 - 4th
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 3, 1),  # Race 2 - 3rd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 4, 1),  # Race 2 - 4th
    ])
    heats.append(heat3)

    # Race 4 - Winner Bracket (Race 1 - 1st, 2nd; Race 2 - 1st, 2nd)
    heat4 = HeatPlan(heat_names[3], [
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 1, 0),  # Race 1 - 1st
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 2, 0),  # Race 1 - 2nd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 1, 1),  # Race 2 - 1st
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 2, 1),  # Race 2 - 2nd
    ])
    heats.append(heat4)

    # Race 5 - Lower Bracket (Race 3 - 1st, 2nd; Race 4 - 3rd, 4th)
    heat5 = HeatPlan(heat_names[4], [
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 1, 2),  # Race 3 - 1st
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 2, 2),  # Race 3 - 2nd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 3, 3),  # Race 4 - 3rd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 4, 3),  # Race 4 - 4th
    ])
    heats.append(heat5)

    # Race 6 - Final (Race 4 - 1st, 2nd; Race 5 - 1st, 2nd)
    heat6 = HeatPlan(heat_names[5], [
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 1, 3),  # Race 4 - 1st
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 2, 3),  # Race 4 - 2nd
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 1, 4),  # Race 5 - 1st
        HeatPlanSlot(SeedMethod.HEAT_INDEX, 2, 4),  # Race 5 - 2nd
    ])
    heats.append(heat6)

    return heats

def register_handlers(args):
    for generator in [
        HeatGenerator(
            "8 Pilot Double Elimination Bracket",
            generate8PilotDEBracketHeats,
            None,
            [
                UIField('race1_qualifiers', "Race 1 qualifiers (comma separated)", UIFieldType.TEXT, value="1,8,4,5"),
                UIField('race2_qualifiers', "Race 2 qualifiers (comma separated)", UIFieldType.TEXT, value="2,7,3,6"),
                UIField('heat_names', "Heat names (comma separated)", UIFieldType.TEXT, value="Race 1,Race 2,Race 3,Race 4,Race 5,Race 6"),
            ]
        ),
    ]:
        args['register_fn'](generator)

def initialize(rhapi):
    rhapi.events.on(Evt.HEAT_GENERATOR_INITIALIZE, register_handlers)

