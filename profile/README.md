# Stellaegis

English · [Français](README.fr.md)

Stellaegis is a family of .NET libraries for the parts business applications have in common: accounts and
rights, documents, transactional email, background jobs, secrets. Each library is a NuGet package published on its
own, so an application references only the ones it needs.

The libraries are written for .NET developers whose application keeps data apart: the data of several organizations
in a multi-tenant service, or the data of a single one. Stellaegis calls the unit of that separation a
**compartment**. Every module isolates its data by compartment in the same way. The application declares its shape
once — a desktop application without a network, a web application for one organization, a multi-tenant service — and
each module reads that declaration instead of being configured for it separately.

The packages target .NET 10. Those that keep a database keep it on PostgreSQL. Identity, Issuer, Access and Registry
also run on SQL Server.

## Repositories

| Repository | Role | Version |
| --- | --- | --- |
| [Stellaegis.Primitives](https://github.com/Stellaegis/Stellaegis.Primitives) | The shared building blocks: results and errors, compartments and actors, a unit of work, database installation, startup checks | 6.1.0 |
| [Stellaegis.Identity](https://github.com/Stellaegis/Stellaegis.Identity) | Accounts: registration, login, second factor, password reset. Issues no token | 9.2.0 |
| [Stellaegis.Issuer](https://github.com/Stellaegis/Stellaegis.Issuer) | The OpenID Connect issuer: tokens, clients, scopes, revocation. Knows no account | 5.5.0 |
| [Stellaegis.Registry](https://github.com/Stellaegis/Stellaegis.Registry) | The catalogue of operations, roles and memberships: what gives a right its meaning | 7.1.2 |
| [Stellaegis.Access](https://github.com/Stellaegis/Stellaegis.Access) | The access decision: an actor, a space, an operation; yes or no | 6.1.2 |
| [Stellaegis.Secrets](https://github.com/Stellaegis/Stellaegis.Secrets) | Reading and writing secrets through one interface, whatever the vault: configuration, an encrypted PostgreSQL table, Scaleway Secret Manager | 5.0.3 |
| [Stellaegis.Caching](https://github.com/Stellaegis/Stellaegis.Caching) | An in-memory cache with a bounded number of entries, group invalidation and metrics | 5.0.2 |
| [Stellaegis.Blobs](https://github.com/Stellaegis/Stellaegis.Blobs) | Storage for binary content, per compartment or in a shared space; a file system adapter | 5.0.2 |
| [Stellaegis.Backplane](https://github.com/Stellaegis/Stellaegis.Backplane) | The internal event bus of an application spread over several processes | 5.1.1 |
| [Stellaegis.Notifications](https://github.com/Stellaegis/Stellaegis.Notifications) | Notifications pushed to the connected clients of a compartment, over SignalR | 5.0.2 |
| [Stellaegis.Operations](https://github.com/Stellaegis/Stellaegis.Operations) | Jobs that run outside a request, launched by a user or scheduled | 5.0.3 |
| [Stellaegis.Rendering](https://github.com/Stellaegis/Stellaegis.Rendering) | Rendering a template to HTML or PDF, with Scriban and Playwright | 5.1.1 |
| [Stellaegis.Documents](https://github.com/Stellaegis/Stellaegis.Documents) | Versioned documents, their content stored through Blobs | 5.1.2 |
| [Stellaegis.Messaging](https://github.com/Stellaegis/Stellaegis.Messaging) | Transactional email, sent through a durable outbox | 5.0.3 |
| [Stellaegis.Trash](https://github.com/Stellaegis/Stellaegis.Trash) | A trash: a deleted object is restored under the same identity, or purged when its deadline passes | 5.0.3 |

All fifteen repositories publish their packages on nuget.org, and the versions above are the ones published there.
None of them is in production use yet.

Versions follow semantic versioning: the major number changes with every breaking change to a contract. The
`CHANGELOG.md` of each repository lists what changed in each version.

## How the repositories fit together

```text
Stellaegis.Primitives                        .NET only
├── Identity · Issuer · Registry · Access    identity and rights
├── Secrets · Caching · Blobs · Backplane · Notifications · Operations · Rendering
└── Documents → Blobs
    Messaging → Secrets, Caching
    Trash
```

Primitives depends on .NET alone, and every other repository depends on it. Dependencies between the other
repositories are few: the ones marked with an arrow above, and two composition packages described below.

Identity and rights are split across four repositories, one question each. Identity says who a person is. Issuer
turns an authenticated person into tokens, without knowing any account. Registry says what a right means. Access
decides. An application composes the ones it uses: `Stellaegis.Registry.Identity` connects Registry to Identity, and
`Stellaegis.Access.Client` relies on Caching.

In every repository, adapters are packages separate from the core: a database engine, ASP.NET Core, an HTTP client.
An application that exposes no web endpoint therefore takes no dependency on ASP.NET Core.

## Known limitations

- **Blobs writes content as it receives it.** Its file system adapter does not encrypt files. Encryption at rest is
  left to the storage, for example volume encryption on the host with BitLocker or LUKS. The key is then the same for
  every compartment.
- **An old encryption key cannot be retired yet.** Secrets, Documents, Messaging and Trash encrypt their data under
  key slots, and a new key is used for new writes. Nothing re-encrypts existing data under the new key yet.
- **No backup and restore guide.** The repositories do not yet describe what a consistent backup contains (the
  databases, the blob storage, the keys kept apart) or the order of a restore.
- **Deployment on Linux, in containers, is not documented.** It requires deciding where two sets of keys are kept —
  those of ASP.NET Core data protection and those of the token issuer — since a container loses them when it
  restarts.
- **No repository provides an audit log.** A logging package designed for the GDPR and the EU AI Act is under study.

## License and contact

All repositories are released under the MIT license.

Contact: [contact@stellaegis.fr](mailto:contact@stellaegis.fr)
