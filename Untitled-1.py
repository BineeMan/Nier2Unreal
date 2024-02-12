
f = open("G:\\NierModding\\Animations\\anims.txt", 'r')
content = f.read()
fileName = "pl0000_0004"
#"     "
index = content.find(fileName)
indexEnd = content.find("\n", index)
generatedName=content[index:indexEnd].replace(" ", "").replace("?", '')
print(generatedName)
f.close()