from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Company, Base, Smartphone, User

engine = create_engine('sqlite:///companysmartphone.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="Yusuke Asai", email="yuyu@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

company1 = Company(user_id=1, name="Apple")

session.add(company1)
session.commit()

smartphone1 = Smartphone(user_id=1, name="iPhone X", description="Adopting OLED screen technology",
                     price="$999", company=company1)
session.add(smartphone1)
session.commit()

smartphone2 = Smartphone(user_id=1, name="iPhone 8", description="The iPhone 8 is a smartphone designed, developed, and marketed by Apple Inc. It was announced on September 12, 2017",
                     price="$600", company=company1)
session.add(smartphone2)
session.commit()

smartphone3 = Smartphone(user_id=1, name="iPhone 7 Plus", description="The iPhone 7's overall design is similar to the iPhone 6S, but introduces new colour options (matte black and jet black), water and dust resistance.",
                     price="$500", company=company1)
session.add(smartphone3)
session.commit()
