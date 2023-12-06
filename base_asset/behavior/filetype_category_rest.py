from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import create_category_model
from .static_category_rest import StaticCategoryRestBehavior

class FileTypeCategoryRestBehavior(StaticCategoryRestBehavior):
  def __init__(self, model_class=create_category_model(), data=None, category_type='filetype'):
    super().__init__(model_class, data, category_type)