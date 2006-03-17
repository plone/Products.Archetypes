"""
Backward compatibility module.
"""
import sys
import generator

sys.modules['Products.generator'] = generator
