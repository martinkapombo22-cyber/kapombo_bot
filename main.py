import sqlite3
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- CONFIGURATION ---
TOKEN = "8029553969:AAEXO5qiduKijjBpMJrCiDOPMUxJfC-XD_Q"
API_URL = "https://socpanel.com/privateApi"
API_KEY = "rfP6cVTRArXCeXCdBWk7pYOueIZmRrODV1RmzuW7Vv7cieTsfw8DNc9WAxUH"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Connexion DB
conn = sqlite3.connect("mediabooster.db", check_same_thread=False)
cursor = conn.cursor()

# --- FONCTION API : RÉCUPÉRER LE PRIX ---
def get_service_price(service_id):
    """Récupère le prix pour 1000 unités via l'API Socpanel"""
    try:
        payload = {"key": API_KEY, "action": "services"}
        r = requests.post(API_URL, data=payload)
        services = r.json()
        
        for s in services:
            if str(s['service']) == str(service_id):
                return float(s['rate']) # Prix pour 1000
        return None
    except:
        return None

# --- GESTIONNAIRE DE COMMANDE AMÉLIORÉ ---
@dp.message_handler()
async def create_order(message: types.Message):
    try:
        # 1. Analyse de l'entrée (Format: ID LIEN QUANTITE)
        parts = message.text.split()
        if len(parts) != 3:
            return 

        service_id, link, quantity = parts[0], parts[1], int(parts[2])

        # 2. Récupérer les infos de l'utilisateur en DB
        cursor.execute("SELECT balance FROM users WHERE id=?", (message.from_user.id,))
        user_data = cursor.fetchone()
        user_balance = user_data[0] if user_data else 0

        # 3. Calcul du coût réel
        rate_per_1000 = get_service_price(service_id)
        
        if rate_per_1000 is None:
            await message.answer("❌ ID de service invalide ou introuvable.")
            return

        total_cost = (rate_per_1000 / 1000) * quantity

        # 4. Vérification du solde
        if user_balance < total_cost:
            await message.answer(
                f"⚠️ **Solde insuffisant !**\n\n"
                f"Coût estimé : {total_cost:.2f} $\n"
                f"Votre solde : {user_balance:.2f} $\n\n"
                f"Veuillez recharger via le menu 'Ajouter des fonds'."
            )
            return

        # 5. Envoi de la commande à Socpanel
        params = {
            "key": API_KEY,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        
        response = requests.post(API_URL, data=params).json()

        if "order" in response:
            # 6. Déduction du solde et mise à jour DB
            new_balance = user_balance - total_cost
            cursor.execute("UPDATE users SET balance = ?, orders = orders + 1 WHERE id = ?", 
                           (new_balance, message.from_user.id))
            
            cursor.execute(
                "INSERT INTO orders(user_id, service, link, quantity, status) VALUES(?,?,?,?,?)",
                (message.from_user.id, service_id, link, quantity, "En cours")
            )
            conn.commit()

            await message.answer(
                f"✅ **Commande validée !**\n\n"
                f"ID Commande : `{response['order']}`\n"
                f"Coût : {total_cost:.2f} $\n"
                f"Nouveau solde : {new_balance:.2f} $",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"❌ Erreur API : {response.get('error', 'Inconnue')}")

    except ValueError:
        await message.answer("⚠️ La quantité doit être un nombre entier.")
    except Exception as e:
        print(f"Erreur : {e}")
        await message.answer("⚠️ Une erreur est survenue lors de la commande.")

# --- LANCEMENT ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
