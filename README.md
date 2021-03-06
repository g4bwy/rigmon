# Dependencies

apt-get install python python-simplejson python-requests


# Setup

Copy pools_config.py.sample to pools_config.py, then edit pools_config.py to set your own credentials:

* username: your MPOS username (which is usually prepended to your worker's logins, eg. 'username.worker')
* base_url: base URL of your pool. OVH and n3rd3d pools are included as examples
* api_uid: the API UID number for your account (can be found under "My Account" / "Edit Account" / "User Id")
* api_key: the API key for your account (can be found under "My Account" / "Edit Account" / "API Key")
* hashfactor: a multiplication factor that is applied to hashrate measurements to get H/m unit (depends on your pool's config. editing is usually not needed)
* sharefactor: same as hashfactor, but for sharerate in shares/minute


Copy worker_groups.py.sample to worker_groups.py, then edit worker_groups.py to set your workers configuration.

Each group is declared as a dict, and the name must match a valid worker name in your pool.

eg. if you declare a group named 'group1' and your pool username is 'foo', you must setup a worker named 'foo.group1' on your pool,
and all declared workers within that group must use that same worker name.

The 'cost' function can optionally be used to compute power/cost consumption for a given worker group, based on a single unit's cost or power consumption (if you don't want to worry about that, just use a function that returns 0).


# Run

    python ./monitor.py <pool name>


