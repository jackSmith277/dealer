print('Testing Python environment...')
import sys
print(f'Python version: {sys.version}')

try:
    import flask
    print(f'Flask version: {flask.__version__}')
except ImportError as e:
    print(f'Error importing Flask: {e}')

try:
    import sqlalchemy
    print(f'SQLAlchemy version: {sqlalchemy.__version__}')
except ImportError as e:
    print(f'Error importing SQLAlchemy: {e}')

try:
    import jwt
    print(f'PyJWT version: {jwt.__version__}')
except ImportError as e:
    print(f'Error importing PyJWT: {e}')

try:
    import passlib
    print(f'passlib version: {passlib.__version__}')
except ImportError as e:
    print(f'Error importing passlib: {e}')

print('Test completed.')