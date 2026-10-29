import traceback

from passlib.context import CryptContext

from database.connection import SessionLocal, check_db_connection
from models.history import History
from models.role import Role
from models.user import User
from models.user_info import UserInfo
from models.user_params import DEFAULT_LAST_COLOR_ID, DEFAULT_PALETTE, UserParams

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3


# =========================
# SEED ROLES
# =========================
def seed_roles(db):
    print("=== SEED ROLES ===")

    roles = [
        (ROLE_ADMIN_ID, "ADMIN", "Administrateur", "Accès complet au système"),
        (ROLE_STAFF_ID, "STAFF", "Membre du staff", "Gestion / support"),
        (ROLE_USER_ID, "USER", "Utilisateur", "Rôle par défaut"),
    ]

    for role_id, code, label, desc in roles:
        role = db.query(Role).filter(Role.id == role_id).first()

        if role:
            role.code = code
            role.label = label
            role.description = desc
            print(f"[OK] Rôle mis à jour : {code} (id={role_id})")
        else:
            role = Role(
                id=role_id,
                code=code,
                label=label,
                description=desc,
            )
            db.add(role)
            print(f"[+] Rôle créé : {code} (id={role_id})")

    db.commit()
    print("=== FIN SEED ROLES ===")


# =========================
# SEED USERS
# =========================
def seed_users(db):
    print("=== SEED USERS ===")

    users = [
        ("admin@harmonia.test", "root", "Admin", "Root", "admin", ROLE_ADMIN_ID),
        ("staff@harmonia.test", "staff123", "Staff", "Op", "staff", ROLE_STAFF_ID),
        ("user@harmonia.test", "user123", "User", "Client", "user", ROLE_USER_ID),
    ]

    for email, password, first, last, username, role_id in users:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            hashed_pw = pwd_context.hash(password)

            user = User(
                email=email,
                password_hash=hashed_pw,
                is_active=True,
                role_id=role_id,
            )
            db.add(user)
            db.flush()  # pour récupérer user.id

            print(f"[+] Utilisateur créé : {email}")
        else:
            print(f"[OK] Utilisateur existant : {email}")

        # -------------------
        # USER INFO
        # -------------------
        if not user.info:
            user_info = UserInfo(
                user_id=user.id,
                first_name=first,
                last_name=last,
                username=username,
                avatar_url=None,
            )
            db.add(user_info)
            print("   → UserInfo créé")
        else:
            user.info.first_name = first
            user.info.last_name = last
            user.info.username = username
            print("   → UserInfo mis à jour")

        # -------------------
        # USER PARAMS (palette)
        # -------------------
        if not user.params:
            user_params = UserParams(
                user_id=user.id,
                color_1=DEFAULT_PALETTE[0],
                color_2=DEFAULT_PALETTE[1],
                color_3=DEFAULT_PALETTE[2],
                last_color_id=DEFAULT_LAST_COLOR_ID,
            )
            db.add(user_params)
            print("   → UserParams créé")
        else:
            # On ne réécrit pas la palette : l'utilisateur peut l'avoir personnalisée
            print("   → UserParams existant (non modifié)")

    db.commit()
    print("=== FIN SEED USERS ===")


# =========================
# SEED HISTORY
# =========================
# Quelques entrées de démo pour l'utilisateur de test, dont des noms longs
# (> 120 caractères) pour vérifier qu'ils ne sont plus coupés.
LONG_PROMPT = (
    "Warm evolving pad with slow filter sweeps, subtle detuned saw layers, "
    "a soft sub bass underneath, gentle chorus and a long airy reverb tail, "
    "slightly dusty and nostalgic, perfect for late night ambient sessions "
    "and cinematic transitions between scenes"
)

HISTORY_SEED = [
    ("Warm pad", "generate", {"cutoff": 0.45, "resonance": 0.20}),
    (
        "make it brighter and add more movement",
        "refine",
        {"cutoff": 0.70, "resonance": 0.25},
    ),
    (LONG_PROMPT, "generate", {"cutoff": 0.35, "resonance": 0.30}),
]


def seed_history(db):
    print("=== SEED HISTORY ===")

    user = db.query(User).filter(User.email == "user@harmonia.test").first()

    if not user:
        print("[SKIP] Utilisateur de test absent")
        return

    for name, type_, params in HISTORY_SEED:
        exists = (
            db.query(History)
            .filter(History.user_id == user.id, History.name == name)
            .first()
        )

        if exists:
            print(f"[OK] Historique existant : {name[:40]}...")
            continue

        db.add(History(user_id=user.id, name=name, type=type_, parameters=params))
        print(f"[+] Historique créé ({len(name)} car.) : {name[:40]}...")

    db.commit()
    print("=== FIN SEED HISTORY ===")


# =========================
# MAIN
# =========================
def main():
    print("========== LANCEMENT SCRIPT DE SEED ==========")

    check_db_connection()

    db = SessionLocal()
    try:
        seed_roles(db)
        seed_users(db)
        seed_history(db)
        print("========== SEED TERMINE ==========")
    except Exception as e:
        db.rollback()
        print("******** ERREUR DANS LE SCRIPT DE SEED ********")
        print(e)
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
