find . -name '*.o' -exec pahole '{}' ';' > structs.txt
