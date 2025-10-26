try:
    from jconfigpy.Dialog import Dialog
    from jconfigpy.Dialog import CMDDialog
    from jconfigpy.ErrorType import FileNotExistError
    from jconfigpy.VariableMonitor import Monitor
    from jconfigpy.Config import JConfig
except ImportError:
    from .Dialog import Dialog
    from .Dialog import CMDDialog
    from .ErrorType import FileNotExistError
    from .VariableMonitor import Monitor
    from .Config import JConfig

