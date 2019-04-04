#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import User, Base, Categories, Items


engine = create_engine('sqlite:///categoriesanditems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

category_1 = Categories(name="IT")

session.add(category_1)
session.commit()

category_2 = Categories(name="Travel")

session.add(category_2)
session.commit()

category_3 = Categories(name="Facilities")

session.add(category_3)
session.commit()

category_4 = Categories(name="General Services")

session.add(category_4)
session.commit()

category_5 = Categories(name="Mechanical Services")

session.add(category_5)
session.commit()

category_6 = Categories(name="Environment")

session.add(category_6)
session.commit()

category_7 = Categories(name="Wind Turbine")

session.add(category_7)
session.commit()

category_8 = Categories(name="Patrimony")

session.add(category_8)
session.commit()

category_9 = Categories(name="Health and Safety")

session.add(category_9)
session.commit()

# User Test
user1 = User(name="Ally Jhonson", email="test@email.com", picture='https://www.google.com/url?sa=i&rct=j&q=&esrc=s&source=images&cd=&cad=rja&uact=8&ved=2ahUKEwjf-9DYnNXgAhWgErkGHSkjCJMQjRx6BAgBEAU&url=http%3A%2F%2Fwww.adorocinema.com%2Ffilmes%2Ffilme-196960%2Fcriticas-adorocinema%2F&psig=AOvVaw24a-TOD_INJEKvLyi90Tvt&ust=1551127044077669')  # noqa

session.add(user1)
session.commit

# Add Item
item1 = Items(item_name="Notebook", category_id="1", description="Avell",
              user_id="0")

session.add(item1)
session.commit()


print("Categories added!")
