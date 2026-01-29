"""
Modulo de fuentes centralizado para CustomTkinter
Reemplaza tkinter.font.Font con CTkFont para compatibilidad
"""
from customtkinter import CTkFont


class _FontsStorage:
    """Almacenamiento interno de fuentes"""
    initialized = False
    TITLE = None
    HEADER = None
    NORMAL = None
    SMALL = None
    CODE_NORMAL = None
    CODE_SMALL = None
    MARKDOWN = None
    PREVIEW = None


def _ensure_fonts_initialized():
    """Inicializa las fuentes si aun no se han creado"""
    if not _FontsStorage.initialized:
        _FontsStorage.TITLE = CTkFont(family="Arial", size=18, weight="bold")
        _FontsStorage.HEADER = CTkFont(family="Arial", size=14, weight="bold")
        _FontsStorage.NORMAL = CTkFont(family="Arial", size=12)
        _FontsStorage.SMALL = CTkFont(family="Arial", size=10)
        _FontsStorage.CODE_NORMAL = CTkFont(family="Consolas", size=11)
        _FontsStorage.CODE_SMALL = CTkFont(family="Consolas", size=10)
        _FontsStorage.MARKDOWN = CTkFont(family="Arial", size=10)
        _FontsStorage.PREVIEW = CTkFont(family="Times New Roman", size=11)
        _FontsStorage.initialized = True


class AppFonts:
    """Fuentes centralizadas de la aplicacion RuneScript"""
    
    # Fuente del editor (se inicializa dinamicamente desde config)
    EDITOR = None
    
    def __getattribute__(self, name):
        # Interceptar acceso a atributos de fuente
        if name in ['TITLE', 'HEADER', 'NORMAL', 'SMALL', 'CODE_NORMAL', 
                    'CODE_SMALL', 'MARKDOWN', 'PREVIEW']:
            _ensure_fonts_initialized()
            return getattr(_FontsStorage, name)
        return super().__getattribute__(name)
    
    @classmethod
    def init_editor_font(cls, family: str, size: int):
        """Inicializa la fuente del editor desde config"""
        cls.EDITOR = CTkFont(family=family, size=size)
        return cls.EDITOR
    
    @classmethod
    def scale_all(cls, factor: float):
        """Escala todas las fuentes por un factor"""
        _ensure_fonts_initialized()
        
        for font in [_FontsStorage.TITLE, _FontsStorage.HEADER, _FontsStorage.NORMAL, 
                     _FontsStorage.SMALL, _FontsStorage.CODE_NORMAL, _FontsStorage.CODE_SMALL,
                     _FontsStorage.MARKDOWN, _FontsStorage.PREVIEW]:
            if font is not None:
                current_size = font.cget('size')
                font.configure(size=int(current_size * factor))
        
        if cls.EDITOR is not None:
            current_size = cls.EDITOR.cget('size')
            cls.EDITOR.configure(size=int(current_size * factor))


# Crear instancia singleton para uso como AppFonts.TITLE, etc.
AppFonts = AppFonts()


def create_font(family: str, size: int, weight: str = "normal",
                slant: str = "roman", underline: bool = False,
                overstrike: bool = False) -> CTkFont:
    """
    Crea una fuente CTkFont con interfaz similar a tkinter.font.Font
    Para facilitar la migracion
    """
    return CTkFont(
        family=family,
        size=size,
        weight=weight,
        slant=slant,
        underline=underline,
        overstrike=overstrike
    )
