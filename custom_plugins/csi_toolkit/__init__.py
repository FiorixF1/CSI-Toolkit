import logging
import RHUtils
from eventmanager import Evt

from .class_rank_brackets.class_rank_brackets     import initialize as class_rank_brackets_initializer
from .csi_export.csi_export                       import initialize as csi_export_initializer
from .ddr_overlays.ddr_overlays                   import initialize as ddr_overlays_initializer
from .generator_8_pilots_de.generator_8_pilots_de import initialize as generator_8_pilots_de_initializer

logger = logging.getLogger(__name__)

def initialize(rhapi):
    class_rank_brackets_initializer(rhapi)
    csi_export_initializer(rhapi)
    ddr_overlays_initializer(rhapi)
    generator_8_pilots_de_initializer(rhapi)
