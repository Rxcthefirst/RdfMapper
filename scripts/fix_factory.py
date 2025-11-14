import os
import shutil

factory_old = "src/rdfmap/generator/matchers/factory.py"
factory_backup = "src/rdfmap/generator/matchers/factory_old_backup.py"
factory_new = "src/rdfmap/generator/matchers/factory_new.py"

# Backup old file
if os.path.exists(factory_old):
    shutil.move(factory_old, factory_backup)
    print(f"Backed up {factory_old} to {factory_backup}")

# Move new file into place
shutil.move(factory_new, factory_old)
print(f"Moved {factory_new} to {factory_old}")
print("Factory.py has been fixed!")

