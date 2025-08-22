
document.addEventListener('DOMContentLoaded',function(){
const quizForm = document.querySelector('#createQuizForm');
if (quizForm) {
    quizForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const form = this;
        const formData = new FormData(form);

        // Collect selected student IDs
        const allowedStudents = Array.from(document.getElementById('allowed_students').selectedOptions)
                                    .map(option => option.value);
        allowedStudents.forEach(id => formData.append('allowed_students[]', id));

        fetch('/createQuiz', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert("Quiz created successfully!");
                form.reset();
                window.location.href = `/add-questions/${result.test_id}`;
            } else {
                alert(result.error || "Failed to create a quiz.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });


    }
    const joinBtn = document.querySelector('#JoinQuiz');
    if (joinBtn) joinBtn.addEventListener('click',() => join_quiz());

    const viewBtn = document.querySelector('#ViewScore');
    if (viewBtn) viewBtn.addEventListener('click',() => view_score());

    const createBtn = document.querySelector('#CreateQuiz');
    if (createBtn) createBtn.addEventListener('click',() => create_quiz());

    const scoreBtn = document.querySelector('#StudentScore');
    if (scoreBtn) scoreBtn.addEventListener('click',() => student_score());




    const joinBtn1 = document.querySelector('#whenJoinQuiz')
    const viewBtn1 = document.querySelector('#whenViewScore')
    const createBtn1 = document.querySelector('#whenCreateQuiz')
    const scoreBtn1 = document.querySelector('#whenStudentScore')

        if (joinBtn1) joinBtn1.style.display = 'none';
        if (viewBtn1) viewBtn1.style.display = 'none';
        if (createBtn1) createBtn1.style.display = 'none';
        if (scoreBtn1) scoreBtn1.style.display = 'none';
})
function join_quiz(){
    document.querySelector('#whenJoinQuiz').style.display = 'block';
    document.querySelector('#whenViewScore').style.display = 'none';

}

function view_score() {
    document.querySelector('#whenJoinQuiz').style.display = 'none';
    document.querySelector('#whenViewScore').style.display = 'block';

    const viewContainer = document.querySelector('#whenViewScore1');
    viewContainer.innerHTML = '';  // Clear old content

    fetch(`/scores`)
    .then(response => response.json())
    .then(quizes => {
        quizes.forEach(single_quiz => {
            const new_quiz = document.createElement('div');
            new_quiz.innerHTML = `
                <h5>${single_quiz.test}</h5>
                <h6>Score: ${single_quiz.score}/${single_quiz.total}</h6>
                <h6>Rank: ${single_quiz.rank}</h6>
            `;
            new_quiz.className = 'list-group-item mb-1 border border-dark px-2';

            new_quiz.addEventListener('click', () => view_the_quiz(single_quiz.id));

            viewContainer.appendChild(new_quiz);
        });
    });
}

function view_the_quiz(testID) {
    window.location.href = `/score/${testID}`;
}



function create_quiz(){
    document.querySelector('#whenCreateQuiz').style.display = 'block';
    document.querySelector('#whenStudentScore').style.display = 'none';

}


function student_score(){
    document.querySelector('#whenCreateQuiz').style.display = 'none';
    document.querySelector('#whenStudentScore').style.display = 'block';
    document.querySelector('#studentList').style.display = 'none';
    // available a list of all tests conducted by the teacher
    // when clicking each test , there shows a list of all the students enrolled in that test rank wise and when clicking 
    // each student loads the score.html

    const viewContainer = document.querySelector('#whenStudentScore1');
    viewContainer.innerHTML = '';  // Clear old content
    fetch(`/progresses`)
    .then(response => response.json())
    .then(progresses => {
        progresses.forEach(single_quiz => {
        new_quiz=document.createElement('div');
        new_quiz.innerHTML=`
        <h5>${single_quiz.title}</h5>
        <h6>appeared/allowed: ${single_quiz.total_students_appeared}/${single_quiz.total_allowed_students}</h6>
        <h6>start-Time / duration: ${formatDate(single_quiz.start_time)} / ${single_quiz.duration_minutes} minutes</h6>
        <h6>RoomID: ${single_quiz.room_id}</h6>
        <h6>testID: ${single_quiz.id}</h6>
        <a href="/visit_test/${single_quiz.id}" class="btn btn-primary mb-2">Visit</a>
        <button class="btn btn-primary mb-2 student-report-btn" data-id="${single_quiz.id}">Student Report</button>
        `;
        function formatDate(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString('en-GB', {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        }
        new_quiz.className='list-group-item mb-1 border border-dark px-2';

        new_quiz.querySelector(".student-report-btn").addEventListener('click', (e) => {
            const quizId = e.target.dataset.id; 
            view_the_student_list(quizId);
        });
        
        viewContainer.append(new_quiz);
        })
    })
}
function view_the_student_list(testID) {
    // Hide other sections
    document.querySelector('#whenCreateQuiz').style.display = 'none';
    document.querySelector('#whenStudentScore').style.display = 'none';
    
    // Show student list section
    const listContainer = document.querySelector('#studentList');
    const listContent = document.querySelector('#studentListContent');
    listContainer.style.display = 'block';

    // Clear previous content
    listContent.innerHTML = '';

    // Fetch students who took the test
    fetch(`/progress/${testID}`)
    .then(response => response.json())
    .then(students => {
        if (students.length === 0) {
            listContent.innerHTML = "<p>No students have attempted this test yet.</p>";
            return;
        }

        students.forEach(student => {
            const div = document.createElement('div');
            div.className = 'list-group-item mb-1 border border-dark px-2';
            div.innerHTML = `
                <h6>Name: ${student.student.username}</h6>
                <p>Score: ${student.score} / ${student.total}</p>
                <p>Rank: ${student.rank}</p>
            `;

            // Add click to view score.html for this student
            div.addEventListener('click', () => {
                window.location.href = `/score/${testID}/${student.id1}`;
            });

            listContent.appendChild(div);
        });
    })
    .catch(error => {
        listContent.innerHTML = "<p>Failed to load student data.</p>";
        console.error(error);
    });
}