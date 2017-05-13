from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Categories, Items, Base, User

engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# add the admin
user = User(name="admin", email="admin@localhost.com", admin=True)
session.add(user)
session.commit()

# Category 1
category1 = Categories(name="Necklaces", picture="static/images/necklace.jpg", user=user)
session.add(category1)
session.commit()

# Add items to category
item1 = Items(name="Red Coral beads necklace", description="Vibrant and lively coral bead necklace", price="$29.99",
              category_id=category1.id, picture="static/images/necklace1.jpg", user=user)
session.add(item1)
session.commit()


# item2 = Items(name="Amethyst necklace", description="Beautiful amethyst necklace", price="15.99",
#               category_id=category1.id,
#               picture="static/images/necklace2.jpg")
#
# session.add(item2)
# session.commit()
#
#item3 = Items(name="Black Onyx necklace", description="Features the shiny & pure blackness of black onyx",
#              price="$15.99", category_id=category1.id, picture="static/images/necklace.jpg")
#session.add(item3)
#session.commit()


# category2 = Categories(name="Bracelets", picture="static/images/necklace.jpg")
#
# session.add(category2)
# session.commit()
#
# item1 = Items(name="black lava bead", description="natural black lava beads 8-10inch", price="$12.99",
#               category_id=category2.id,
#               picture="static/images/necklace.jpg")
# session.add(item1)
# session.commit()
#
# item2 = Items(name="Macrame bracelet", description="beautiful handmade Macrame bracelet", price="$10.99",
#               category_id=category2.id, picture="static/images/necklace.jpg")
# session.add(item2)
# session.commit()
#
# category3 = Categories(name="Earrings", picture="static/images/earrings.jpg")
#
# session.add(category1)
# session.commit()
#
# item1 = Items(name="Pearl earrings", description="natural fresh water pearl earrings", price="$12.99",
#               category_id=category3.id, picture="static/images/necklace.jpg")
# session.add(item1)
# session.commit()
#
# item2 = Items(name="Red coral earrings", description="handmade red coral dangle earrings", price="$13.50",
#               category_id=category3.id, picture="static/images/necklace.jpg")
# session.add(item2)
# session.commit()
#

print "Added items"