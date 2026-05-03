from server import app
import uvicorn
def main():
    uvicorn.run(app,host="localhost",port=8000)

main()   