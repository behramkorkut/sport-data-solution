"""Présence d'un conftest.py à la racine : pytest ajoute ce dossier au
sys.path (mode d'import "prepend" par défaut), ce qui rend le package
`src` importable depuis les tests, indépendamment de la config pythonpath.
"""
