"""Configurações do projeto CorteCerto.

Valores sensíveis e dependentes do ambiente vêm de variáveis de ambiente
ou do arquivo .env local, que não é versionado.
"""

import os
from pathlib import Path

import dj_database_url
from django.contrib.messages import constants as niveis_mensagem
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(nome, padrao):
    valor = os.environ.get(nome, "").strip().lower()
    if valor == "":
        return padrao
    return valor in {"1", "true", "yes", "sim"}


def env_lista(nome, padrao=""):
    bruto = os.environ.get(nome, padrao)
    return [item.strip() for item in bruto.split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Defina DJANGO_SECRET_KEY no arquivo .env "
        "ou nas variáveis de ambiente."
    )

DEBUG = env_bool("DJANGO_DEBUG", False)

if not DEBUG and SECRET_KEY.startswith("troque-esta-chave"):
    raise ImproperlyConfigured(
        "Use uma DJANGO_SECRET_KEY própria quando DJANGO_DEBUG for False."
    )

ALLOWED_HOSTS = env_lista(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)

CSRF_TRUSTED_ORIGINS = env_lista("DJANGO_CSRF_TRUSTED_ORIGINS")

# Endereço do admin.
ADMIN_URL = (
    os.environ.get("DJANGO_ADMIN_URL", "").strip().strip("/")
    or "admin"
) + "/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "agenda",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cortecerto.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cortecerto.wsgi.application"
ASGI_APPLICATION = "cortecerto.asgi.application"

# PostgreSQL em produção; SQLite no ambiente local.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": (
                os.environ.get("DJANGO_DB_PATH", "").strip()
                or BASE_DIR / "db.sqlite3"
            ),
            "OPTIONS": {"transaction_mode": "IMMEDIATE"},
        }
    }

# Períodos de atendimento.
# Formato: "HH:MM-HH:MM,HH:MM-HH:MM".
PERIODOS_ATENDIMENTO = os.environ.get(
    "CORTECERTO_PERIODOS_ATENDIMENTO", ""
).strip()

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]

# Autenticação.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "agenda:inicio"
LOGOUT_REDIRECT_URL = "login"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Arquivos estáticos.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if DATABASE_URL
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Classes de alerta do Bootstrap.
MESSAGE_TAGS = {niveis_mensagem.ERROR: "danger"}

# Segurança de transporte e cookies.
USAR_HTTPS = env_bool("DJANGO_HTTPS", not DEBUG)

SESSION_COOKIE_SECURE = USAR_HTTPS
CSRF_COOKIE_SECURE = USAR_HTTPS
SECURE_SSL_REDIRECT = USAR_HTTPS

if USAR_HTTPS:
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# Sessões e cookies.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS encaminhado pelo proxy do Render.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
