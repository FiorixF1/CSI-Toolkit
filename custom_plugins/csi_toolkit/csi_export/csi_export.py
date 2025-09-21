from eventmanager import Evt
from .csi_export_impl import CSIExport


def initialize(rhapi):
    #fpvscores = FPVScores(rhapi)
    csi_export = CSIExport(rhapi)
    
    rhapi.events.on(Evt.STARTUP, csi_export.init_plugin)  

    rhapi.events.on(Evt.CLASS_ADD, csi_export.init_ui, priority = 20)
    rhapi.events.on(Evt.CLASS_DUPLICATE, csi_export.init_ui, priority = 20)
    rhapi.events.on(Evt.CLASS_ALTER, csi_export.init_ui, priority = 50)
    rhapi.events.on(Evt.CLASS_DELETE, csi_export.init_ui)

    #rhapi.events.on(Evt.HEAT_GENERATE, fpvscores.heat_listener, priority = 99)
    #rhapi.events.on(Evt.HEAT_ALTER, fpvscores.heat_listener)
    #rhapi.events.on(Evt.HEAT_DELETE, fpvscores.heat_delete)

    #rhapi.events.on(Evt.PILOT_ADD, fpvscores.pilot_listener, priority = 99)
    #rhapi.events.on(Evt.PILOT_ALTER, fpvscores.pilot_listener)
    ##rhapi.events.on(Evt.PILOT_DELETE, fpvscores.pilot_listener)

    #rhapi.events.on(Evt.LAPS_SAVE, fpvscores.results_listener)
    #rhapi.events.on(Evt.LAPS_RESAVE, fpvscores.results_listener)

    rhapi.events.on(Evt.DATA_EXPORT_INITIALIZE, csi_export.register_handlers)