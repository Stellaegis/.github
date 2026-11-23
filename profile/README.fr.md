# Stellaegis

[English](README.md) · Français

Stellaegis est une famille de bibliothèques .NET qui fournit les parties communes d'une application métier : les
comptes et les droits, les documents, l'envoi d'e-mails, les tâches de fond, les secrets. Chaque bibliothèque est un
paquet NuGet publié à part, et une application ne prend que ceux dont elle a besoin.

Ces bibliothèques s'adressent aux développeurs .NET dont l'application sépare des données : celles de plusieurs
organisations dans un service multi-tenant, ou celles d'une seule. Stellaegis appelle **compartiment** l'unité de
cette séparation. Chaque module tient la séparation par compartiment de la même façon, et l'application déclare une
seule fois la forme qu'elle a : application de bureau sans réseau, application web pour une seule organisation,
service multi-tenant. Les modules lisent cette déclaration au lieu d'être configurés chacun pour elle.

Les paquets ciblent .NET 10. Ceux qui tiennent une base de données la tiennent sur PostgreSQL. Identity, Issuer,
Access et Registry la tiennent aussi sur SQL Server.

## Les dépôts

| Dépôt | Rôle | Version |
| --- | --- | --- |
| [Stellaegis.Primitives](https://github.com/Stellaegis/Stellaegis.Primitives) | Les briques communes : résultats et erreurs, compartiments et acteurs, unité de travail, installation des bases, contrôles au démarrage | 6.1.0 |
| [Stellaegis.Identity](https://github.com/Stellaegis/Stellaegis.Identity) | Les comptes : inscription, connexion, second facteur, réinitialisation du mot de passe. N'émet aucun jeton | 9.2.0 |
| [Stellaegis.Issuer](https://github.com/Stellaegis/Stellaegis.Issuer) | L'émetteur OpenID Connect : jetons, clients, scopes, révocation. Ne connaît aucun compte | 5.5.0 |
| [Stellaegis.Registry](https://github.com/Stellaegis/Stellaegis.Registry) | Le catalogue des opérations, les rôles et les appartenances : ce qui donne un sens à un droit | 7.1.2 |
| [Stellaegis.Access](https://github.com/Stellaegis/Stellaegis.Access) | La décision d'accès : un acteur, un espace, une opération ; oui ou non | 6.1.2 |
| [Stellaegis.Secrets](https://github.com/Stellaegis/Stellaegis.Secrets) | Lire et écrire des secrets par une seule interface, quel que soit le coffre : configuration, table PostgreSQL chiffrée, Scaleway Secret Manager | 5.0.3 |
| [Stellaegis.Caching](https://github.com/Stellaegis/Stellaegis.Caching) | Un cache en mémoire au nombre d'entrées borné, avec invalidation par groupe et métriques | 5.0.2 |
| [Stellaegis.Blobs](https://github.com/Stellaegis/Stellaegis.Blobs) | Le stockage de contenu binaire, rangé par compartiment ou dans un espace partagé ; un adaptateur pour le système de fichiers | 5.0.2 |
| [Stellaegis.Backplane](https://github.com/Stellaegis/Stellaegis.Backplane) | Le bus d'événements interne d'une application répartie sur plusieurs processus | 5.1.1 |
| [Stellaegis.Notifications](https://github.com/Stellaegis/Stellaegis.Notifications) | Les notifications poussées vers les clients connectés d'un compartiment, par SignalR | 5.0.2 |
| [Stellaegis.Operations](https://github.com/Stellaegis/Stellaegis.Operations) | Les tâches exécutées hors d'une requête : lancées par un utilisateur, ou planifiées | 5.0.3 |
| [Stellaegis.Rendering](https://github.com/Stellaegis/Stellaegis.Rendering) | Le rendu d'un modèle en HTML ou en PDF, avec Scriban et Playwright | 5.1.1 |
| [Stellaegis.Documents](https://github.com/Stellaegis/Stellaegis.Documents) | Des documents versionnés, dont le contenu est stocké par Blobs | 5.1.2 |
| [Stellaegis.Messaging](https://github.com/Stellaegis/Stellaegis.Messaging) | L'envoi d'e-mails transactionnels, par une file d'envoi durable | 5.0.3 |
| [Stellaegis.Trash](https://github.com/Stellaegis/Stellaegis.Trash) | Une corbeille : un objet supprimé se restaure sous la même identité, ou se purge à son échéance | 5.0.3 |

Les quinze dépôts publient leurs paquets sur nuget.org, et les versions du tableau sont celles qui y sont publiées.
Aucun n'est encore en service en production.

Les versions suivent le versionnage sémantique : le numéro majeur change à chaque rupture de contrat. Le
`CHANGELOG.md` de chaque dépôt dit ce qui a changé à chaque version.

## Comment les dépôts s'articulent

```text
Stellaegis.Primitives                        .NET seul
├── Identity · Issuer · Registry · Access    l'identité et les droits
├── Secrets · Caching · Blobs · Backplane · Notifications · Operations · Rendering
└── Documents → Blobs
    Messaging → Secrets, Caching
    Trash
```

Primitives ne dépend que de .NET, et tous les autres dépôts dépendent de lui. Entre les autres dépôts, les dépendances
sont rares : celles que marque une flèche dans le schéma, et deux paquets de composition décrits ci-dessous.

L'identité et les droits sont répartis en quatre dépôts, un par question. Identity dit qui est une personne. Issuer
transforme une personne authentifiée en jetons, sans connaître les comptes. Registry dit ce que signifie un droit.
Access décide. L'application compose ceux qu'elle emploie : `Stellaegis.Registry.Identity` relie Registry à Identity,
et `Stellaegis.Access.Client` s'appuie sur Caching.

Dans chaque dépôt, les adaptateurs sont des paquets distincts du cœur : un moteur de base de données, ASP.NET Core, un
client HTTP. Une application qui n'expose pas de route web ne dépend donc pas d'ASP.NET Core.

## Limites connues

- **Blobs écrit le contenu tel qu'il le reçoit.** Son adaptateur pour le système de fichiers ne chiffre pas les
  fichiers. Le chiffrement au repos revient au stockage, par exemple le chiffrement du volume de l'hôte avec BitLocker
  ou LUKS. La clé est alors la même pour tous les compartiments.
- **Une ancienne clé de chiffrement ne peut pas encore être retirée.** Secrets, Documents, Messaging et Trash
  chiffrent leurs données sous des emplacements de clé, et une nouvelle clé sert aux nouvelles écritures. Rien ne
  rechiffre encore les données existantes vers la nouvelle clé.
- **Aucun guide de sauvegarde et de restauration.** Les dépôts ne décrivent pas encore ce que contient une sauvegarde
  cohérente (les bases, le stockage des blobs, les clés gardées à part) ni l'ordre d'une restauration.
- **Le déploiement sous Linux, en conteneurs, n'est pas documenté.** Il demande de décider où gardent leurs clés la
  protection des données d'ASP.NET Core et l'émetteur de jetons, qu'un conteneur perd à son redémarrage.
- **Aucun dépôt ne fournit de journal d'audit.** Un paquet de journalisation conforme au RGPD et à l'AI Act est à
  l'étude.

## Licence et contact

Tous les dépôts sont publiés sous licence MIT.

Contact : [contact@stellaegis.fr](mailto:contact@stellaegis.fr)
