"""
Nepal's 7 provinces and 77 districts (current federal structure, effective since
the 2015 constitution; Koshi/Madhesh/etc. are the post-2023 official names).
Used to validate checkout addresses are real Nepal locations, and to build the
Province -> District dropdowns on the frontend from a single source of truth.
"""

NEPAL_PROVINCES = {
    "Koshi": [
        "Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang", "Okhaldhunga",
        "Panchthar", "Sankhuwasabha", "Solukhumbu", "Sunsari", "Taplejung", "Terhathum", "Udayapur",
    ],
    "Madhesh": [
        "Bara", "Dhanusha", "Mahottari", "Parsa", "Rautahat", "Saptari", "Sarlahi", "Siraha",
    ],
    "Bagmati": [
        "Bhaktapur", "Chitwan", "Dhading", "Dolakha", "Kathmandu", "Kavrepalanchok", "Lalitpur",
        "Makwanpur", "Nuwakot", "Ramechhap", "Rasuwa", "Sindhuli", "Sindhupalchok",
    ],
    "Gandaki": [
        "Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang", "Myagdi",
        "Nawalpur", "Parbat", "Syangja", "Tanahun",
    ],
    "Lumbini": [
        "Arghakhanchi", "Banke", "Bardiya", "Dang", "Eastern Rukum", "Gulmi", "Kapilvastu",
        "Palpa", "Parasi", "Pyuthan", "Rolpa", "Rupandehi",
    ],
    "Karnali": [
        "Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot", "Mugu",
        "Salyan", "Surkhet", "Western Rukum",
    ],
    "Sudurpashchim": [
        "Achham", "Baitadi", "Bajhang", "Bajura", "Dadeldhura", "Darchula", "Doti", "Kailali", "Kanchanpur",
    ],
}


def is_valid_district(province: str, district: str) -> bool:
    return district in NEPAL_PROVINCES.get(province, [])


def is_valid_postal_code(code: str) -> bool:
    """Nepal Post uses plain 5-digit numeric codes (e.g. 44600). Format check only —
    this doesn't look up the specific ~900 assigned codes, just rejects anything
    that clearly isn't a Nepal postal code (letters, wrong length, non-digits).
    Empty string is allowed since postal codes are commonly omitted in Nepal."""
    if not code:
        return True
    return code.isdigit() and len(code) == 5
