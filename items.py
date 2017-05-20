from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Categories, Items, Base, User

engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# add the admin/super_user
user = User(name="admin", email="admin@localhost.com", admin=True)
session.add(user)
session.commit()

# Category 1
category1 = Categories(name="Necklaces", picture="static/images/necklace.jpg",
                       description="Handmade with utmost care & attention, be it a choker, a long necklace or anything in between",
                       user=user)
session.add(category1)
session.commit()

#  Add items to category
item1 = Items(name="Red Coral beads necklace", description="Vibrant and lively coral bead necklace", price="$29.99",
              category_id=category1.id, picture="static/images/necklace1.jpg", user=user)
session.add(item1)
session.commit()



print "Added items"