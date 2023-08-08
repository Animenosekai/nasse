---
version: 2.0
status: BETA
---

# Next

> Provides information about the next coming version

This version provides general improvements over the whole project, brining more stability and ease of use.

> **Warning**
> This is a breaking update !

The endpoints modelling objects are now slightly different. Most of them support method variation, which lets the app developer change the endpoint definition for different methods.

Also, this comes with several changes in how the models attributes and parameters are managed. Please look at the new models' definition before updating.

## New

- Docs Localization: You can now choose a language for the automatic documentation generation (please contribute to add your language!)
  - It already comes with the English, Japanese and French translations
- A new logging system, which is way more stable
- A new string formatting system
- A new server configuration system
- Switch to a local variables based system (more stable)
- Using [`rich`](https://github.com/Textualize/rich) to output things to the console, which improves the UI a lot
- Adding a CLI to easily run Nasse apps
- Adding a TUI to test endpoints, similar to Postman
- Starting to add debug endpoints, when the server is running in `DEBUG` mode
- Add a way of giving a sub category to endpoints
- Improving endpoint definitions, letting the developer the ability to document them with a Python-native approach (a big part of it can be directly extracted from the function definition)
- Introducing a new server backend based system to run the server, which allows the user to actually specify if they want to use *Gunicorn* or any other WSGI compatible server backend. (this fixes a pretty big bug where people on Windows couldn't really run their server)

## Fixes

- Fixing a problem with CORS headers
- Fixing a problem with request verifications
- Fixing an issue with `UserSent` validation
- Fixing an issue with the Windows operating system

## Updates

- Using *dataclasses* for endpoint models
- Using `pyproject.toml`
- Using correct versioning
- Using [poetry](https://python-poetry.org)
- Only log exceptions when wanted
- Better compatibility
- Improved code quality
- Improved in-code docs
- Using the `perf_counter` clock instead of the `process_time` one for better results
- Type-hinting code more
- The `Args` utility is more complete
- Making a fully custom `NasseJSONEncoder` with more flexibility (example: encoding default types)
- Other little improvements

Everything is detailed in the [`README.md`](./README.md) file

A comparison from the previous release can be found here [`v1.1...v2.0`](https://github.com/Animenosekai/nasse/compare/v1.1...v2.0)

A comparison from the current branch can be found here [`v2.0...main`](https://github.com/Animenosekai/nasse/compare/v2.0...main)

> 🍡 Animenosekai
