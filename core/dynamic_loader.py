import importlib  # <- ten import musi być!

def load_components(registry):
    loaded_components = []
    for item in registry:
        module = importlib.import_module(item["module"])
        class_ = getattr(module, item["class"])
        loaded_components.append(class_())
    return loaded_components

engine_registry = [
    {"module": "core.engines.ryzykant", "class": "RyzykantEngine"},
    {"module": "core.engines.agresywny", "class": "AgresywnyEngine"},
]

engines = load_components(engine_registry)
