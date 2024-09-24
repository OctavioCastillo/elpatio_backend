import smtplib
from config import Config

class Mail:

    def __init__(self) -> None:
        self.__connection = smtplib.SMTP("smtp.gmail.com")
        self.__connection.starttls()
        self.__connection.login(user=str(Config.EMAIL), password=str(Config.PASSWORD))
        
    def send_verification_email(self, email, link):
        subject = "Verificacion de correo electronico"
        body = f"Por favor verifica tu correo haciendo clic en el siguiente enlace: {link}"
        message = f"Subject: {subject}\n\n{body}"
        self.__connection.sendmail(from_addr=Config.EMAIL, to_addrs=email, msg=message)

    def close(self):
        self.__connection.quit()