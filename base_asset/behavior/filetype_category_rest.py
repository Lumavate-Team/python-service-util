from sqlalchemy import or_, cast, VARCHAR, func
from app import db
import os
import re
import json
from ..models import CategoryModel
from .static_category_rest import StaticCategoryRestBehavior

class FileTypeCategoryRestBehavior(StaticCategoryRestBehavior):
  def __init__(self, model_class=CategoryModel, data=None):
    super().__init__(model_class, data, 'filetype')