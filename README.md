<h1 align="center">Falcon</h1>
All in one platform for intercity bus operators

<img src="https://github.com/gurupratap-matharu/midware/blob/master/staticfiles/img/hero.jpg" alt="drawing" width="1920"/>

[![codecov](https://codecov.io/gh/gurupratap-matharu/falcon/branch/master/graph/badge.svg?token=DOIZxrPhqc)](https://codecov.io/gh/gurupratap-matharu/falcon)

### Demo

[Live](https://falconhunt.xyz)

### Documentation

[Documentation](https://gurupratap-matharu.github.io/falcon/)

### Development setup 🛠

Steps to locally setup development after cloning the project.

Create a virtualenv with python 3.10+ and activate it

```bash
python -m venv venv
source venv/bin/activate
```

Then start the server with

```bash
make build
```

This single command should

- Install all your dependencies
- Make and apply all DB migrations
- Spin up a server running on port 8000

### Testing 🧪

    We use the classic unit test framework to run django tests testing each endpoint
    The broad approach is to create mock data for each test with setup and check specific
    test case. Although in production scenario you would add integration or End to end testing.

    To run the entire test suite in one go simply run

```bash
make test
```

### CI/CD? ♾️

    You can actually run our continous integration by executing

```bash
make ci
```

    This should run

    - formatting pipeline
    - linting pipeline
    - testing
    - coverage

### Coverage 🎪

    The CI pipeline itself runs all the tests for the project and generates an html report
    in the root directory of the project.

### Admin Interface 👩‍💼

- For convenience we have access to an admin interface provided by django.
- All data models are hooked up to the admin interface to verify if data has been correctly
  populated in the database.
- But to access the admin you would need to create a super user by running the following

```
make superuser
```

Provide a username, password, email and then you can access admin at http://localhost:8000/admin/

### Features ✨

- Uses logging module quite frequently for easy debugging
- Unit tests to verify functionality as per requirements
- Fast response time
- Make file for faster setup and reusability
