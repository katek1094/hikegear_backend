from .models import Profile

def xd():
    profiles = Profile.objects.all()
    for profile in profiles:
        priv = profile.private_gear
        x = 0
        for cat in priv:
            print(cat)
            for item in cat['items']:
                print(item)
                item['id'] = x
                x += 1
        print(priv)
        profile.private_gear = priv
        profile.save()
