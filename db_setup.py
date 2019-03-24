from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__='user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id' : self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
        }

class Categories(Base):
    __tablename__= 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            
        }

class Items(Base):
    __tablename__='items'

    id = Column(Integer, primary_key=True)
    item_name = Column(String(80), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category_name = Column(String(80))
    category = relationship(Categories)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'item_name': self.item_name,
            'category_id': self.category_id,
            'category_name':self.category_name,
            'description': self.description,
            'user_id': self.user_id,
        }

engine = create_engine('sqlite:///categoriesanditems.db')
Base.metadata.create_all(engine)
print('Congrats, your DB was successfully set up!') 

