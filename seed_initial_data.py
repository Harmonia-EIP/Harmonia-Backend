import traceback

from database.connection import SessionLocal, check_db_connection
from models.role import Role
from models.user import User
from models.user_info import UserInfo
from models.user_params import UserParams  # <-- import des paramètres utilisateur
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3

DEFAULT_LAYOUT_ID = 1  # Layout par défaut
DEFAULT_THEME_ID  = 1  # Thème par défaut (ex: Dark)


def seed_roles(db):
    print("=== SEED ROLES ===")

    roles = [
        (ROLE_ADMIN_ID, "ADMIN", "Administrateur", "Accès complet au système"),
        (ROLE_STAFF_ID, "STAFF", "Membre du staff", "Gestion / support"),
        (ROLE_USER_ID, "USER", "Utilisateur", "Rôle par défaut"),
    ]

    for role_id, code, label, desc in roles:
        existing = db.query(Role).filter(Role.id == role_id).first()
        if existing:
            existing.code = code
            existing.label = label
            existing.description = desc
            db.commit()
            print(f"[OK] Rôle déjà existant : {code} (id={role_id})")
            continue

        role = Role(
            id=role_id,
            code=code,
            label=label,
            description=desc,
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        print(f"[+] Rôle créé : {code} (id={role_id})")

    print("=== FIN SEED ROLES ===")


def seed_users(db):
    print("=== SEED USERS ===")

    users = [
        ("admin@harmonia.test", "admin123", "Admin", "Root", "admin", ROLE_ADMIN_ID),
        ("staff@harmonia.test", "staff123", "Staff", "Op", "staff", ROLE_STAFF_ID),
        ("user@harmonia.test", "user123", "User", "Client", "user", ROLE_USER_ID),
    ]

    for email, password, first, last, username, role_id in users:

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[OK] Utilisateur déjà existant : {email}")
            continue

        hashed_pw = pwd_context.hash(password)

        # --- Création utilisateur ---
        user = User(
            email=email,
            password_hash=hashed_pw,
            is_active=True,
            role_id=role_id,
        )
        db.add(user)
        db.flush()  # <-- pour récupérer user.id

        # --- Infos utilisateur ---
        info = UserInfo(
            user_id=user.id,
            first_name=first,
            last_name=last,
            username=username,
        )
        db.add(info)

        # --- Paramètres utilisateur par défaut ---
        user_params = UserParams(
            user_id=user.id,
            layout_id=DEFAULT_LAYOUT_ID,
            theme_id=DEFAULT_THEME_ID
        )
        db.add(user_params)

        db.commit()
        db.refresh(user)

        role_code = "ADMIN" if role_id == ROLE_ADMIN_ID else "STAFF" if role_id == ROLE_STAFF_ID else "USER"
        print(f"[+] Utilisateur créé : {email} — rôle = {role_code} (id={role_id})")

    print("=== FIN SEED USERS ===")


def main():
    print("========== LANCEMENT SCRIPT DE SEED ==========")

    check_db_connection()

    db = SessionLocal()
    try:
        seed_roles(db)
        seed_users(db)
        print("========== SEED TERMINE ==========")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("******** ERREUR DANS LE SCRIPT DE SEED ********")
        print(e)
        traceback.print_exc()
