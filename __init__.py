def classFactory(iface):
    from .crear_red_electrica import ElectricNetworkPlugin
    return ElectricNetworkPlugin(iface)
