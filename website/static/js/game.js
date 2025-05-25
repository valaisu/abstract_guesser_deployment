// Global variables
let currentPaper = null;
let roundScores = [];
let currentRound = 1;
const totalRounds = 7;
let totalScore = 0;
let gameActive = false;

// DOM Elements
const paperAbstractEl = document.getElementById('paper-abstract');
const dateGuessEl = document.getElementById('date-guess');
const submitGuessBtn = document.getElementById('submit-guess');
const currentScoreEl = document.getElementById('current-score');
const currentRoundEl = document.getElementById('current-round');
const resultFeedbackEl = document.getElementById('result-feedback');
const userGuessDateEl = document.getElementById('user-guess-date');
const actualDateEl = document.getElementById('actual-date');
const dateDifferenceEl = document.getElementById('date-difference');
const roundScoreEl = document.getElementById('round-score');
const nextRoundBtn = document.getElementById('next-round');
const gameOverEl = document.getElementById('game-over');
const finalScoreEl = document.getElementById('final-score');
const roundScoresListEl = document.getElementById('round-scores-list');
const playAgainBtn = document.getElementById('play-again');
const highScoreEl = document.getElementById('high-score');

// Initialize the game
function initGame() {
    fetchPaper()
        .then(() => {
            gameActive = true;
            currentRound = 1;
            totalScore = 0;
            roundScores = [];
            
            updateScoreDisplay();
            updateRoundDisplay();
            
            // Set today's date as the default value for the date picker
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];
            dateGuessEl.value = formattedDate;
            
            // Hide result feedback if visible
            resultFeedbackEl.classList.add('hidden');
            
            dateGuessEl.disabled = false;
            submitGuessBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error initializing game:', error);
            paperAbstractEl.textContent = 'Error loading paper. Please try again.';
        });
}

// Fetch a paper from the server
async function fetchPaper() {
    try {
        const response = await fetch('/game/fetch-paper');
        if (!response.ok) {
            throw new Error('Failed to fetch paper');
        }
        
        currentPaper = await response.json();
        
        // Display the abstract
        paperAbstractEl.textContent = currentPaper.abstract;
        
        console.log('Paper loaded. Date:', currentPaper.date);
    } catch (error) {
        console.error('Error fetching paper:', error);
        throw error;
    }
}

// Handle a guess
async function handleGuess() {
    if (!gameActive) return;
    
    const guessDate = dateGuessEl.value;
    
    if (!guessDate) {
        alert('Please select a date');
        return;
    }
    
    try {
        const response = await fetch('/game/calculate-score', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                actual_date: currentPaper.date,
                guess_date: guessDate
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to calculate score');
        }
        
        const result = await response.json();
        
        // Store the round score
        const roundScore = result.score;
        roundScores.push({
            round: currentRound,
            guess: guessDate,
            actual: result.actual_date,
            difference: result.difference_days,
            score: roundScore
        });
        
        // Update total score
        totalScore += roundScore;
        updateScoreDisplay();
        
        // Show result feedback
        showRoundResult(guessDate, result.actual_date, result.difference_days, roundScore);
        
        // Disable inputs until next round
        dateGuessEl.disabled = true;
        submitGuessBtn.disabled = true;
        
    } catch (error) {
        console.error('Error submitting guess:', error);
        alert('Error submitting guess. Please try again.');
    }
}

// Show round result
function showRoundResult(guessDate, actualDate, differenceDays, score) {
    // Format dates for display
    const formattedGuessDate = formatDateForDisplay(guessDate);
    const formattedActualDate = formatDateForDisplay(actualDate);
    
    // Format difference as days or years
    let differenceText;
    if (differenceDays === 0) {
        differenceText = 'Perfect match!';
    } else if (differenceDays === 1) {
        differenceText = '1 day';
    } else if (differenceDays < 30) {
        differenceText = `${differenceDays} days`;
    } else if (differenceDays < 365) {
        const months = Math.round(differenceDays / 30);
        differenceText = `About ${months} month${months > 1 ? 's' : ''}`;
    } else {
        const years = (differenceDays / 365).toFixed(1);
        differenceText = `About ${years} year${years !== '1.0' ? 's' : ''}`;
    }
    
    // Display the results
    userGuessDateEl.textContent = formattedGuessDate;
    actualDateEl.textContent = formattedActualDate;
    dateDifferenceEl.textContent = differenceText;
    roundScoreEl.textContent = score;
    
    // Show the result feedback
    resultFeedbackEl.classList.remove('hidden');
}

// Format date for display (YYYY-MM-DD to Month DD, YYYY)
function formatDateForDisplay(dateStr) {
    // Handle different date formats that might come from the server
    let date;
    
    if (dateStr.length <= 7) {
        // Format is YYYY-MM
        date = new Date(dateStr + '-01');
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
    } else {
        // Format is YYYY-MM-DD
        date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }
}

// Handle next round
function handleNextRound() {
    if (currentRound >= totalRounds) {
        endGame();
    } else {
        currentRound++;
        updateRoundDisplay();
        
        // Fetch a new paper
        fetchPaper()
            .then(() => {
                // Reset UI for next round
                resultFeedbackEl.classList.add('hidden');
                dateGuessEl.disabled = false;
                submitGuessBtn.disabled = false;
            })
            .catch(error => {
                console.error('Error fetching paper for next round:', error);
                alert('Error loading paper. Please try again.');
            });
    }
}

// Update the score display
function updateScoreDisplay() {
    currentScoreEl.textContent = totalScore;
}

// Update the round display
function updateRoundDisplay() {
    currentRoundEl.textContent = currentRound;
}

// End the game
function endGame() {
    gameActive = false;
    
    // Show game over screen
    finalScoreEl.textContent = totalScore;
    
    // Display round breakdown
    roundScoresListEl.innerHTML = '';
    roundScores.forEach(round => {
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>Round ${round.round}:</strong> 
            You guessed ${formatDateForDisplay(round.guess)}, 
            actual was ${formatDateForDisplay(round.actual)} 
            (${round.score} points)
        `;
        roundScoresListEl.appendChild(li);
    });
    
    // Submit score to server if logged in
    submitScore();
    
    // Show game over screen
    gameOverEl.classList.remove('hidden');
}

// Submit score to server
async function submitScore() {
    try {
        const response = await fetch('/game/submit-score', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ score: totalScore })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(data.message);
            
            // Update high score if available
            if (highScoreEl && data.message === 'New high score!') {
                highScoreEl.textContent = totalScore;
            }
        }
    } catch (error) {
        console.error('Error submitting score:', error);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Set min/max dates for the date picker
    const today = new Date();
    const formattedToday = today.toISOString().split('T')[0];
    dateGuessEl.max = formattedToday;
    dateGuessEl.min = '2010-01-01'; // Minimum date is 2010-01-01
    
    // Start the game when the page loads
    initGame();
    
    // Handle submit button click
    submitGuessBtn.addEventListener('click', handleGuess);
    
    // Handle next round button
    nextRoundBtn.addEventListener('click', handleNextRound);
    
    // Handle play again button
    playAgainBtn.addEventListener('click', () => {
        gameOverEl.classList.add('hidden');
        initGame();
    });
});