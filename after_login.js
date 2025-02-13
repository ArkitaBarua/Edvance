function handleClick(role) {
    if (role === 'student') {
        alert('You selected Student!');
        window.location.href = 'level.html'; // This will navigate to level.html
    } else if (role === 'parent_teacher') {
        alert('You selected Parent/Teacher!');
    }
}
