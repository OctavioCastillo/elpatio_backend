import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

class Mail:

    def __init__(self) -> None:
        self.EMAIL = os.getenv("EMAIL")
        self.PASSWORD = os.getenv("PASSWORD")
        self.HOST = os.getenv("HOST")
        self.__connection = smtplib.SMTP("smtp.gmail.com")
        self.__connection.starttls()
        self.__connection.login(user=str(self.EMAIL), password=str(self.PASSWORD))
        
    def send_verification_email(self, email, token):
        subject = "Verificacion de correo electronico"
        body = f"Por favor verifica tu correo haciendo clic en el siguiente enlace: {self.HOST}/{token}"
        message = f"Subject: {subject}\n\n{body}"
        self.__connection.sendmail(from_addr=self.EMAIL, to_addrs=email, msg=message)

    def close(self):
        self.__connection.quit()