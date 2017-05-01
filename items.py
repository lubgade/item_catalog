from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Categories, Items, Base

engine = create_engine('sqlite:///jewelrydb.db')

#Base.metadata.drop_all(engine)
#Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Category 1
category1 = Categories(name="Necklaces")

session.add(category1)
session.commit()

item1 = Items(name="Red Coral beads necklace", description="Vibrant and lively coral bead necklace", price="$29.99",
              category=category1, picture="")

session.add(item1)
session.commit()

item2 = Items(name="Amethyst necklace", description="Beautiful amethyst necklace", price="15.99", category=category1,
              picture="")

session.add(item2)
session.commit()

item3 = Items(name="Black Onyx necklace", description="Features the shiny & pure blackness of black onyx",
              price="$15.99", category=category1, picture="")
session.add(item3)
session.commit()


category2 = Categories(name="Bracelets")

session.add(category2)
session.commit()

item1 = Items(name="black lava bead", description="natural black lava beads 8-10inch", price="$12.99", category=category2,
              picture="")
session.add(item1)
session.commit()

item2 = Items(name="Macrame bracelet", description="beautiful handmade Macrame bracelet", price="$10.99",
              category=category2)
session.add(item2)
session.commit()

category3 = Categories(name="Earrings")

session.add(category1)
session.commit()

item1 = Items(name="Pearl earrings", description="natural fresh water pearl earrings", price="$12.99",
              category=category3)
session.add(item1)
session.commit()

item2 = Items(name="Red coral earrings", description="handmade red coral dangle earrings", price="$13.50",
              category=category3)
session.add(item2)
session.commit()


print "Added items"