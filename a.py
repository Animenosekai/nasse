from nasse.utils.sanitize import to_path

print(to_path("hello_world_how_are_You__man__"))
print(to_path("hello_world_how_are_You__man__this_seemsCool"))
print(to_path("hELlo_world_how_are_You__user_name__hey_this_seemsCool"))
print(to_path("hELlo_world_how_are_You_hey__user_name__hey_this_seemsCool"))
