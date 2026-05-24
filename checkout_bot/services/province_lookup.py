from __future__ import annotations


_PROVINCE_MAP: dict[str, str] = {
    "Agrigento": "AG", "Alessandria": "AL", "Ancona": "AN", "Aosta": "AO",
    "Arezzo": "AR", "Ascoli Piceno": "AP", "Asti": "AT", "Avellino": "AV",
    "Bari": "BA", "Barletta-Andria-Trani": "BT", "Belluno": "BL", "Benevento": "BN",
    "Bergamo": "BG", "Biella": "BI", "Bologna": "BO", "Bolzano": "BZ",
    "Brescia": "BS", "Brindisi": "BR", "Cagliari": "CA", "Caltanissetta": "CL",
    "Campobasso": "CB", "Caserta": "CE", "Catania": "CT", "Catanzaro": "CZ",
    "Chieti": "CH", "Como": "CO", "Cosenza": "CS", "Cremona": "CR",
    "Crotone": "KR", "Cuneo": "CN", "Enna": "EN", "Fermo": "FM",
    "Ferrara": "FE", "Firenze": "FI", "Foggia": "FG", "Forlì-Cesena": "FC",
    "Frosinone": "FR", "Genova": "GE", "Gorizia": "GO", "Grosseto": "GR",
    "Imperia": "IM", "Isernia": "IS", "La Spezia": "SP", "L'Aquila": "AQ",
    "Latina": "LT", "Lecce": "LE", "Lecco": "LC", "Livorno": "LI",
    "Lodi": "LO", "Lucca": "LU", "Macerata": "MC", "Mantova": "MN",
    "Massa-Carrara": "MS", "Matera": "MT", "Messina": "ME", "Milano": "MI",
    "Modena": "MO", "Monza e Brianza": "MB", "Napoli": "NA", "Novara": "NO",
    "Nuoro": "NU", "Oristano": "OR", "Padova": "PD", "Palermo": "PA",
    "Parma": "PR", "Pavia": "PV", "Perugia": "PG", "Pesaro e Urbino": "PU",
    "Pescara": "PE", "Piacenza": "PC", "Pisa": "PI", "Pistoia": "PT",
    "Pordenone": "PN", "Potenza": "PZ", "Prato": "PO", "Ragusa": "RG",
    "Ravenna": "RA", "Reggio Calabria": "RC", "Reggio Emilia": "RE", "Rieti": "RI",
    "Rimini": "RN", "Roma": "RM", "Rovigo": "RO", "Salerno": "SA",
    "Sassari": "SS", "Savona": "SV", "Siena": "SI", "Siracusa": "SR",
    "Sondrio": "SO", "Sud Sardegna": "SU", "Taranto": "TA", "Teramo": "TE",
    "Terni": "TR", "Torino": "TO", "Trapani": "TP", "Trento": "TN",
    "Treviso": "TV", "Trieste": "TS", "Udine": "UD", "Varese": "VA",
    "Venezia": "VE", "Verbano-Cusio-Ossola": "VB", "Vercelli": "VC", "Verona": "VR",
    "Vibo Valentia": "VV", "Vicenza": "VI", "Viterbo": "VT",
}


def get_province_code(province_name: str) -> str:
    code = _PROVINCE_MAP.get(province_name, "")
    if not code:
        raise KeyError(f"unknown Italian province: {province_name!r}")
    return code
