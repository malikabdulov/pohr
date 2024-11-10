// Хранение предыдущих значений ползунков
const previousValues = {
    technical_skills: 50,
    soft_skills: 30,
    cultural_fit: 10,
    growth_potential: 10
};

// Функция для обновления весов и управления состоянием кнопки
function updateWeights(event) {
    const sliderId = event.target.id;
    const technicalSkills = parseInt(document.getElementById("technical_skills").value);
    const softSkills = parseInt(document.getElementById("soft_skills").value);
    const culturalFit = parseInt(document.getElementById("cultural_fit").value);
    const growthPotential = parseInt(document.getElementById("growth_potential").value);

    // Рассчитываем текущую сумму весов
    let total = technicalSkills + softSkills + culturalFit + growthPotential;

    // Если сумма превышает 100, откатываем значение ползунка к предыдущему допустимому значению
    if (total > 100) {
        document.getElementById(sliderId).value = previousValues[sliderId];
        // Пересчитываем общую сумму после отката
        total = previousValues.technical_skills + previousValues.soft_skills + previousValues.cultural_fit + previousValues.growth_potential;
    } else {
        // Если сумма не превышает 100, обновляем предыдущее значение ползунка
        previousValues[sliderId] = parseInt(document.getElementById(sliderId).value);
    }

    // Обновляем значения отображения рядом с ползунками
    document.getElementById("technical_skills_value").textContent = `${document.getElementById("technical_skills").value}%`;
    document.getElementById("soft_skills_value").textContent = `${document.getElementById("soft_skills").value}%`;
    document.getElementById("cultural_fit_value").textContent = `${document.getElementById("cultural_fit").value}%`;
    document.getElementById("growth_potential_value").textContent = `${document.getElementById("growth_potential").value}%`;

    // Обновляем общий индикатор суммы
    document.getElementById("totalIndicator").textContent = `${total}%`;

    // Управляем состоянием кнопки и цветом индикатора
    const rankButton = document.querySelector(".btn-primary");
    if (total === 100) {
        document.getElementById("totalIndicator").style.color = "#007bff";
        rankButton.disabled = false;
        rankButton.style.backgroundColor = "#007bff"; // Активный синий цвет
    } else {
        document.getElementById("totalIndicator").style.color = "#6c757d";
        rankButton.disabled = true;
        rankButton.style.backgroundColor = "#6c757d"; // Серый цвет
    }
}

// Подключаем функцию к каждому ползунку
document.getElementById("technical_skills").addEventListener("input", updateWeights);
document.getElementById("soft_skills").addEventListener("input", updateWeights);
document.getElementById("cultural_fit").addEventListener("input", updateWeights);
document.getElementById("growth_potential").addEventListener("input", updateWeights);

// Обработка выбора вакансии и загрузка её описания
document.getElementById("vacancy").addEventListener("change", function () {
    const vacancyId = this.value;
    if (vacancyId) {
        fetch(`/get_vacancy_details/${vacancyId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error("Ошибка:", data.error);
                } else {
                    // Отображаем и заполняем описание вакансии
                    document.getElementById("vacancyDetails").style.display = "block";
                    document.getElementById("vacancyTitle").textContent = data.title;
                    document.getElementById("vacancyExperience").textContent = data.experience;
                    document.getElementById("vacancySkills").textContent = data.skills;
                    document.getElementById("vacancyEducation").textContent = data.education;
                }
            })
            .catch(error => console.error("Ошибка при получении данных вакансии:", error));
    } else {
        document.getElementById("vacancyDetails").style.display = "none";
    }
});



// Данные кандидата с оценками и объяснением
const candidateData = {
    labels: ["Технические навыки", "Soft skills", "Культурное соответствие", "Потенциал роста"],
    scores: [95, 85, 80, 90],
    explanations: [
        "Обладает более чем 7 годами опыта в разработке сложных backend-решений.",
        "Демонстрирует менторство младшим разработчикам, что указывает на хорошие навыки коммуникации.",
        "Соответствует корпоративной культуре, готовность к переезду и обсуждению удаленной работы.",
        "Большой опыт и навыки позволяют предположить высокий потенциал для развития."
    ],
    colors: ["#28a745", "#17a2b8", "#ffc107", "#007bff"]
};


function generate_cover_letter(channel, jobDescription, candidateName) {
    fetch('/generate_cover_letter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            channel: channel,
            job_description: jobDescription,
            candidate_name: candidateName
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message); // Отображение сообщения, полученного от сервера
    })
    .catch(error => console.error('Ошибка:', error));
}