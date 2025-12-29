import traceback

from database.connection import SessionLocal, check_db_connection
from models.role import Role
from models.user import User
from models.user_info import UserInfo
from models.user_role import UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_roles(db):
    print("=== SEED ROLES ===")

    roles = [
        ("ADMIN", "Administrateur", "Accès complet au système"),
        ("STAFF", "Membre du staff", "Gestion / support"),
        ("USER", "Utilisateur", "Rôle par défaut"),
    ]

    for code, label, desc in roles:
        existing = db.query(Role).filter(Role.code == code).first()

        if existing:
            print(f"[OK] Rôle déjà existant : {code}")
            continue

        role = Role(
            code=code,
            label=label,
            description=desc,
        )
        db.add(role)
        db.commit()
        db.refresh(role)

        print(f"[+] Rôle créé : {code}")

    print("=== FIN SEED ROLES ===")


def seed_users(db):
    print("=== SEED USERS ===")

    users = [
        ("admin@harmonia.test", "admin123", "Admin", "Root", "admin", "ADMIN"),
        ("staff@harmonia.test", "staff123", "Staff", "Op", "staff", "STAFF"),
        ("user@harmonia.test", "user123", "User", "Client", "user", "USER"),
    ]

    for email, password, first, last, username, role_code in users:

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[OK] Utilisateur déjà existant : {email}")
            continue

        role = db.query(Role).filter(Role.code == role_code).first()
        if not role:
            print(f"[ERR] Rôle manquant : {role_code}, utilisateur ignoré : {email}")
            continue

        hashed_pw = pwd_context.hash(password)

        user = User(
            email=email,
            password_hash=hashed_pw,
            is_active=True,
        )
        db.add(user)
        db.flush()  # récupère user.id

        info = UserInfo(
            user_id=user.id,
            first_name=first,
            last_name=last,
            username=username,
        )
        db.add(info)

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db.add(user_role)

        db.commit()
        db.refresh(user)

        print(f"[+] Utilisateur créé : {email} — rôle = {role_code}")

    print("=== FIN SEED USERS ===")


def main():
    print("========== LANCEMENT SCRIPT DE SEED ==========")

    # vérifie la connexion & crée les tables si absentes
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
