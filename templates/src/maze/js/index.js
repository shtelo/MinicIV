const padding = 200, mazePadding = 20;
const canvas = document.querySelector("#canvas");
const context = canvas.getContext("2d");
const mainContainer = document.querySelector("#main-container");
const successWindow = document.querySelector("#success-window");
const successCode = document.querySelector("#success-code");
const successCommand = document.querySelector("#success-command");

const fps = 60;

const getMaze = async () => {
    const response = await fetch('/maze/get');
    return response.json();
};

const getMazeCode = async () => {
    const response = await fetch('/maze/get-code');
    return response.json();
};

const clicks = [
    new Audio('/src/audio/20210509017.wav'),
    new Audio('/src/audio/20210509018.wav'),
    new Audio('/src/audio/20210509019.wav'),
    new Audio('/src/audio/20210509020.wav')
];

let cells = [];
let mazeColumnCount, mazeRowCount;
let cellSize;
let mazeCanvas, mazeContext;
let mazeX, mazeY;
let mazeCode;
let codeDelta = 0;

let mouseX, mouseY,
    mouseDown = false;

let currentX = 0,
    currentY = 0;
let displayX = 0,
    displayY = 0;
let history = [];

let notUpdated = true;
let started = false;

class Cell {
    constructor(x, y, left, right, top, down) {
        this.x = x;
        this.y = y;
        this.left = left;
        this.right = right;
        this.top = top;
        this.bottom = down;
    }

    draw() {
        mazeContext.beginPath();
        if (this.left) {
            mazeContext.moveTo(mazePadding / 2 + this.x * cellSize, mazePadding / 2 + this.y * cellSize);
            mazeContext.lineTo(
                mazePadding / 2 + this.x * cellSize,
                mazePadding / 2 + cellSize + this.y * cellSize
            );
        }
        if (this.right) {
            mazeContext.moveTo(mazePadding / 2 + cellSize + this.x * cellSize, mazePadding / 2 + this.y * cellSize);
            mazeContext.lineTo(
                mazePadding / 2 + cellSize + this.x * cellSize,
                mazePadding / 2 + cellSize + this.y * cellSize
            );
        }
        if (this.top) {
            mazeContext.moveTo(mazePadding / 2 + this.x * cellSize, mazePadding / 2 + this.y * cellSize);
            mazeContext.lineTo(mazePadding / 2 + cellSize + this.x * cellSize, mazePadding / 2 + this.y * cellSize);
        }
        if (this.bottom) {
            mazeContext.moveTo(mazePadding / 2 + this.x * cellSize, mazePadding / 2 + cellSize + this.y * cellSize);
            mazeContext.lineTo(
                mazePadding / 2 + cellSize + this.x * cellSize,
                mazePadding / 2 + cellSize + this.y * cellSize
            );
        }
        mazeContext.stroke();
    }
}

function getCellX(x) {
    return mazeX + x * cellSize + cellSize / 2 + mazePadding / 2;
}

function getCellY(y) {
    return mazeY + y * cellSize + cellSize / 2 + mazePadding / 2;
}

function cursorInMazeX() {
    return Math.floor((mouseX - mazePadding / 2 - mazeX) / cellSize);
}

function cursorInMazeY() {
    return Math.floor((mouseY - mazePadding / 2 - mazeY) / cellSize);
}

function getDirection(x, y) {
    if (currentY === y) {
        if (x - currentX === -1) return 'LEFT';
        if (x - currentX === 1) return 'RIGHT';
    } else if (currentX === x) {
        if (y - currentY === -1) return 'UP';
        if (y - currentY === 1) return 'DOWN';
    }
    return null;
}

function isCanGoTo(x, y) {
    const direction = getDirection(x, y);
    const cell = cells[currentX + currentY * mazeColumnCount];

    if (direction === 'LEFT') return !cell.left;
    else if (direction === 'RIGHT') return !cell.right;
    else if (direction === 'UP') return !cell.top;
    else if (direction === 'DOWN') return !cell.bottom;
    return false;
}

function arraysEqual(a1, a2) {
    /* WARNING: arrays must not contain {objects} or behavior may be undefined */
    return JSON.stringify(a1) === JSON.stringify(a2);
}

function getSuccessCode() {
    let result = mazeCode;
    history.forEach(value => {
        result += `${value[0]}.${value[1]} - `;
    });
    return md5(result.substr(0, result.length - 3));
}

function copySuccessCode() {
    successCode.select();
    document.execCommand('copy');
    notUpdated = false;
    successWindow.style.display = 'none';
    mainContainer.style.filter = 'none';
}

function tick() {
    if (started) {
        if (currentX === mazeColumnCount - 1 && currentY === mazeRowCount - 1 && notUpdated) {
            successWindow.style.display = 'block';
            mainContainer.style.filter = 'blur(3px)';
            successCode.value = `$미로 ${getSuccessCode()}`;
            successCommand.innerHTML = successCode.value;
            notUpdated = false;
        } else {
            let x = cursorInMazeX(),
                y = cursorInMazeY();
            if (isCanGoTo(x, y)) {
                if (arraysEqual(history[history.length - 1], [x, y])) {
                    history.pop();
                } else {
                    history.push([currentX, currentY]);
                }
                currentX = x;
                currentY = y;
                clicks[Math.floor(Math.random() * clicks.length)].play();
            }
        }

        displayX += (currentX - displayX) / 6;
        displayY += (currentY - displayY) / 6;

        codeDelta++;
        if (codeDelta > fps) {
            codeDelta -= fps;
            getMazeCode().then(value => {
                if (value.code !== mazeCode) {
                    location.reload();
                }
            });
        }
    } else {
        if (mouseDown) {
            started = true;
        }
    }
}

function render() {
    context.fillStyle = "#2c2c2c";
    context.fillRect(0, 0, canvas.width, canvas.height);

    if (started) {
        context.strokeStyle = '#6ccccc';
        context.beginPath();
        context.arc(getCellX(displayX), getCellY(displayY), cellSize / 4, 0, 2 * Math.PI);
        context.stroke();
        context.beginPath();

        if (currentX !== mazeColumnCount - 1 || currentY !== mazeRowCount - 1) {
            context.strokeStyle = '#fdde59';
            context.moveTo(mouseX, mouseY);
            context.lineTo(getCellX(displayX), getCellY(displayY));
            context.stroke();
        }

        for (let i = currentX !== mazeColumnCount - 1 || currentY !== mazeRowCount - 1 ? Math.max(1, history.length - 2) : 1; i < history.length; i++) {
            context.strokeStyle = "fdde59";
            context.beginPath();
            context.moveTo(getCellX(history[i - 1][0]), getCellY(history[i - 1][1]));
            context.lineTo(getCellX(history[i][0]), getCellY(history[i][1]));
            context.stroke();
        }
        if (history.length > 0) {
            context.strokeStyle = "fdde59";
            context.beginPath();
            context.moveTo(getCellX(history[history.length - 1][0]), getCellY(history[history.length - 1][1]));
            context.lineTo(getCellX(displayX), getCellY(displayY));
            context.stroke();
        }

        try {
            context.drawImage(mazeCanvas, mazeX, mazeY);
        } catch (DOMException) {
        }

        context.fillText(mazeCode, 100, 100);
    } else {
        context.strokeStyle = '#f7f7f9';
        context.strokeRect(mazeX + mazePadding / 2, mazeY + mazePadding / 2, cellSize * mazeRowCount, cellSize * mazeColumnCount);
    }
}

function readyMazeCanvas() {
    cellSize = (Math.min(canvas.width, canvas.height) - padding) / Math.max(mazeColumnCount, mazeRowCount);
    mazeCanvas = document.createElement("canvas");
    mazeCanvas.width = cellSize * mazeColumnCount + mazePadding;
    mazeCanvas.height = cellSize * mazeRowCount + mazePadding;
    mazeX = (canvas.width - cellSize * mazeColumnCount) / 2;
    mazeY = (canvas.height - cellSize * mazeRowCount) / 2;
    mazeContext = mazeCanvas.getContext("2d");
    mazeContext.lineWidth = 2;
    mazeContext.strokeStyle = "#f7f7f9";
    cells.forEach(cell => {
        cell.draw();
    });
}

getMaze().then(value => {
    value['board'].forEach(line => {
        line.forEach(cell => {
            let data = cell.split(":");
            let position = data[0].split("."), borders = data[1];
            cells.push(
                new Cell(
                    parseInt(position[0]), parseInt(position[1]),
                    borders.charAt(0) === "1",
                    borders.charAt(1) === "1",
                    borders.charAt(2) === "1",
                    borders.charAt(3) === "1"
                )
            );
        });
    });
    mazeColumnCount = value['width'];
    mazeRowCount = value['height'];
    mazeCode = value['code'];

    readyMazeCanvas();
});

window.addEventListener("resize", (() => {
    let result = event => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        readyMazeCanvas();
    };
    result();
    return result
})());

window.addEventListener("mousemove", event => {
    mouseX = event.clientX;
    mouseY = event.clientY;
});

window.addEventListener("mousedown", event => {
    if (event.button === 0) {
        mouseDown = true;
    }
});

window.addEventListener("mouseup", event => {
    if (event.button === 0) {
        mouseDown = false;
    }
});

setInterval(() => {
    tick();
    render();
}, 1000 / fps);