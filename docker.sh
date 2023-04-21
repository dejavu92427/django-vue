docker-compose build
# docker-compose run service-django sh -c "django-admin startproject project ." 在本地手key這段（第一次要重建）
docker-compose up
# docker rmi test-app

#======django init
# python manage.py makemigrations 
# python manage.py migrate
# python manage.py loaddata initial_data 用於初始化或填充資料庫，並且只在開發或測試階段使用