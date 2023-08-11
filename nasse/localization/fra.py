"""
The french translation

Copyright
---------
Animenosekai
    Original Author, MIT License
"""

from nasse.localization.base import Localization


class FrenchLocalization(Localization):
    """
    The french translation for the docs generation
    """
    __native__ = "Français"

    sections = "Sections"
    getting_started = "Pour commencer"

    yes = "Oui"
    no = "Non"

    no_description = "Il n'y a pas de description"
    using_method = "En utilisant {method}"

    # Authentication
    authentication = "Authentification"
    no_auth_rule = "Il n'y a pas de règle d'authentification définie"
    no_login = "Il n'est **pas** nécessaire d'être authentifié"
    login_with_types_required = "Il est **nécessaire** d'être authentifié avec un compte {types}"
    login_with_types_required = "Il est **optionnel** d'être authentifié avec un compte {types}"
    login_required = "Il est **nécessaire** d'être authentifié"
    login_optional = "Il est **optionnel** d'être authentifié"
    login_suffix_only_verified = " (mais l'authentification est seulement vérifié et le compte ne sera pas cherché)"

    # User sent values
    parameters = "Paramètres"
    headers = "En-têtes"
    cookies = "Cookies"
    dynamic_url = "URL Dynamique"

    name = "Nom"
    description = "Description"
    required = "Obligatoire"
    type = "Type"

    # Example
    example = "Exemple"

    # Response
    response = "Réponse"
    example_response = "Exemple de réponse"
    not_json_response = "Cet endpoint ne semble pas retourner de réponse formatté en JSON."

    # Response description
    returns = "Retourne"
    field = "Champ"
    nullable = "Peut être `null`"

    # Errors
    possible_errors = "Erreurs possibles"
    exception = "Erreur"
    code = "Code"

    # Index
    index = "Index"
    return_to_index = "Retourner à l'Index"

    # Postman
    postman_description = "Tous les endpoints sous la section '{section}' de l'interface API de {name}"

    # Headers
    getting_started_header = '''
# Référence d'API pour {name}

Bienvenue sur la référence d'API pour {name}.

## Globalité

### Format de réponse

Généralement, les réponses JSON seront formattez comme suit (même lorsque des erreurs critiques sont encontrées)

```json
{{
    "success": true,
    "message": "Ça marche!",
    "error": null,
    "data": {{}}
}}
```

| Champ        | Description                                      | Peut être `null` |
| ------------ | ------------------------------------------------ | ---------------- |
| `success`    | Si la requête est un succès ou pas               | Non            |
| `message`    | Un message qui décrit ce qu'il s'est passé       | Oui             |
| `error`      | Le nom de l'erreur si il y en a une              | Oui             |
| `data`       | Des données supplémentaires, les informations demandées | Non            |

### Erreurs

De multiples erreurs peuvent survenir, que ce soit du côté client (au niveau de la requête) ou du côté du serveur.

Les erreurs spécifiques sont documentés dans chaque *Endpoint* mais celles-ci sont celles qui peuvent survenir sur n'importe quel endpoint :

| Erreur                      | Description                                                                                                     | Code  |
| --------------------------- | --------------------------------------------------------------------------------------------------------------- | ----- |
| `SERVER_ERROR`              | Quand une erreur survient sur {name} en traitant la requête.                                                    | 500   |
| `MISSING_CONTEXT`           | Quand dans le code vous essayez d'accéder à une ressource seulement disponible dans un contexte Nasse (pendant une requête) mais que vous n'êtes pas dans un contexte Nasse.       | 500   |
| `INTERNAL_SERVER_ERROR`     | Quand une erreur critique survient sur le système                                                               | 500   |
| `METHOD_NOT_ALLOWED`        | Quand vous faites une requête avec le mauvaise méthode HTTP                                                     | 405   |
| `CLIENT_ERROR`              | Quand quelque chose manque où n'est pas bon avec la requête                                                     | 400   |
| `INVALID_TYPE`              | Quand Nasse n'a pas pu convertir la valeur qui a été envoyée dans le bon type                                   | 400   |
| `MISSING_VALUE`             | Quand quelque chose manque à la requête                                                                         | 400   |
| `MISSING_PARAM`             | Quand un paramètre manque à la requête                                                                          | 400   |
| `MISSING_DYNAMIC`           | Quand une valeur dynamique de l'URL manque                                                                      | 400   |
| `MISSING_HEADER`            | Quand un en-tête manque à la requête                                                                            | 400   |
| `MISSING_COOKIE`            | Quand un cookie manque à la requête                                                                             | 400   |
| `AUTH_ERROR`                | Quand une erreur d'authentification survient                                                                    | 403   |

### Requêtes authentifiées

Quand un utilisateur doit être connecter, l'en-tête "Authorization" doit être définie avec le token de connexion communiqué lorsqu'il s'est connecté.

Vous pouvez aussi utiliser le paramètre "{id}_token" ou le cookie "__{id}_token" mais ceux-ci ne vont pas être priorisé.

Si la règle d'authentification de l'*endpoint* est défini comme "seulement vérifié", le compte ne doit pas être cherché dans la base de donnée mais la forme du token ou des informations comprises à l'intérieur peuvent être vérifiées.

### Mode de développement

Lorsque le mode de développement est activé (`-d` ou `--debug`), de multiples informations sont renvoyées dans la section `debug` des réponses et le niveau `DEBUG` de logging est sélectioné sur le serveurr.

La section 'debug' est disponible sur tous type d'erreur, sauf celles qui sont renvoyées par Flask de manière interne (comme `INTERNAL_SERVER_ERROR`, `METHOD_NOT_ALLOWED`, etc.). En effet, celles-ci doivent modifier le moins possible la requête pour ne pas se retrouver avec une autre erreur qui pourrait survenir)

Le champ "call_stack" est activé seulement quand il y a le paramètre `call_stack` qui est envoyé avec la requête.

```json
{{
    "success": true,
    "message": "Nous n'avons pas pu satisfaire la requête",
    "error": null,
    "data": {{
        "username": "Animenosekai"
    }},
    "debug": {{
        "time": {{
            "global": 0.036757,
            "verification": 0.033558,
            "authentication": 0.003031,
            "processing": 4.9e-05,
            "formatting": 0.0001
        }},
        "ip": "127.0.0.1",
        "headers": {{
            "Host": "api.{id}.com",
            "Connection": "close",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-fr",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
        }},
        "values": {{}},
        "domain": "api.{id}.com",
        "logs": [
            "1636562693.036563｜[INFO] [nasse.receive.Receive.__call__] → Incoming GET request to /account/name from 127.0.0.1",
            "1636562693.070008｜[ERROR] [nasse.exceptions.base.MissingToken.__init__] An authentication token is missing from the request"
        ],
        "call_stack": [
            "pass the 'call_stack' parameter to get the call stack"
        ]
    }}
}}
```

'''

    section_header = '''
# Référence de la section {name}

Ce fichier liste et explique les différents *endpoints* disponible sous la section {name}
'''

    # TUI

    # Footer
    tui_history = "Historique"
    tui_result = "Résultat"
    tui_explorer = "Explorateur"
    tui_submit = "Envoyer"
    tui_options = "Options"
    tui_quit = "Quitter"

    # History
    # WARNING: This should stay under 3 characters to avoid having styling issues
    tui_min = "Min"
    tui_average = "Moy"
    tui_max = "Max"

    # Explorer
    tui_reset = "Réinitialiser"

    # Request
    tui_request = "Requête"
    tui_name = "nom"
    tui_value = "valeur"
    tui_path = "chemin"
    # tui_parameters = "Parameters"
    # tui_headers = "Headers"
    # tui_cookies = "Cookies"
    tui_file = "Fichier"
    tui_add_file = "Ajouter un fichier"
    tui_data = "Donnée"
    tui_add_data_file = "Ajouter un fichier de données"

    # Options
    tui_language = "Langue"
    tui_language_notice = "Vous devez relancer l'application pour que les changements prennent effet"
    tui_base_url = "URL de base"
    tui_base_url_placeholder = "L'URL de base pour les requêtes et l'explorateur"
    tui_endpoints_update = "Mise à jour des endpoints"
    tui_endpoints_update_placeholder = "Fréquence de mise à jour des endpoints pour l'explorateur (sec.)"
    tui_history_limit = "Limite d'historique"
    tui_history_limit_placeholder = "Le nombre maximale de requêtes dans l'historique"
    tui_timeout = "Limite de temps"
    tui_timeout_placeholder = "Limite de temps pour le traitement d'une requête (sec.)"
    tui_redirects = "Redirection"
    tui_allow_redirects = "Autoriser les redirections"
    tui_proxies = "Proxies"
    tui_security = "Sécurité"
    tui_verify_request = "Vérification des requêtes"
    tui_certificate_files = "Certificats"
    tui_add_certificate = "Ajouter un certificat"

    # Result
    tui_start_prompt = "Commencez par envoyer une requête"
    tui_content = "Contenu"
    tui_no_content = "Impossible d'afficher le contenu"
    tui_contacting = "Appel de {url}"
    tui_files = "Fichiers"
    tui_error = "Erreur"

    # File Explorer
    tui_filter = "Filtre"

    # Quit
    tui_quit_confirmation = "Voulez-vous vraiment quitter ?"
    tui_cancel = "Revenir"
