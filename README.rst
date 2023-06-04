=====
Foundation
=====

Foundation is a Django app to conduct web-based basic foundation models.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "foundation" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'foundation',
    ]

2. Include the foundation URLconf in your project urls.py like this::

    path('foundation/', include("foundation.api.urls", namespace="foundation-api")),

3. Run ``python manage.py migrate`` to create the foundation models.

4. Start the development server and visit http://127.0.0.1:8000/admin/.

5. Visit http://127.0.0.1:8000/foundation/ to participate in the foundation.
