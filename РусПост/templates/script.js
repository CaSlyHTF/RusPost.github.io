
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Список пользователей</title>
</head>
<body>
    <h1>Список пользователей</h1>
    <ul id="users"></ul>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const userList = document.getElementById("users");

            // Функция для получения данных пользователей с API
            function loadUsers() {
                fetch("https://example.com/api/users") // Замените на ваш API
                    .then(response => {
                        if (!response.ok) {
                            throw new Error("Сеть не ответила должным образом");
                        }
                        return response.json();
                    })
                    .then(users => {
                        // Заполняем список пользователей
                        users.forEach(user => {
                            const userItem = document.createElement("li");
                            userItem.textContent = `${user.name} (${user.email})`;
                            userList.appendChild(userItem);
                        });
                    })
                    .catch(error => {
                        console.error("Ошибка:", error);
                        const errorItem = document.createElement("li");
                        errorItem.textContent = "Не удалось загрузить пользователей";
                        userList.appendChild(errorItem);
                    });
            }

            // Загружаем пользователей при загрузке страницы
            loadUsers();
        });
    </script>
</body>
</html>

