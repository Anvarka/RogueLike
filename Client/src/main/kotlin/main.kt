import com.googlecode.lanterna.input.KeyType
import com.googlecode.lanterna.screen.TerminalScreen
import com.googlecode.lanterna.terminal.DefaultTerminalFactory
import com.googlecode.lanterna.terminal.swing.SwingTerminalFontConfiguration
import com.googlecode.lanterna.TerminalSize
import io.ktor.application.*
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.features.json.*
import io.ktor.client.features.json.serializer.*
import io.ktor.client.request.*
import io.ktor.response.*
import io.ktor.routing.*
import io.ktor.server.engine.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.delay

enum class State {
    WAIT,
    ACTIVE
}

class Client(private val user: String,
             private val screen: TerminalScreen,
             private val client: HttpClient,
             private val server: String) {
    private var map: Map
    var state: State
    val conditionVariable: Channel<Unit> = Channel(0)

    init {
        connect()
        map = getMapInit()
        state = State.WAIT
    }

    fun gameLoop() {
        while (true) {
            if (map.gameOver) {
                screen.clear()
                val graphics = screen.newTextGraphics()
                graphics.putString(4, 10, "Game Over!")
                screen.refresh()
                screen.readInput()
                return
            }
            screen.drawMap(map, user)
            System.err.println("CHECK STATE: ${state == State.ACTIVE}")
            while (state != State.ACTIVE) runBlocking {
                System.err.println("WAITING !!!")
                conditionVariable.receive()
            }
            System.err.println("WAIT INPUT !!!")

            // Повтор движений
            val key = screen.readInput()
            if (key.keyType == KeyType.Escape || key.keyType == KeyType.EOF) {
                return
            }
            if (key.keyType != KeyType.Character) {
                continue
            }
            val dir = when (key.character) {
                'w' -> Direction.UP
                's' -> Direction.DOWN
                'a' -> Direction.LEFT
                'd' -> Direction.RIGHT
                else -> continue
            }
            state = State.WAIT
            map = move(dir)
            runBlocking {
                delay(100)
            }
        }
    }

    private fun connect() {
        runBlocking {
            client.post<Unit>("$server/server/connect/") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun getMapInit(): Map {
        return runBlocking {
            client.post("$server/server/map/") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun move(dir: Direction): Map {
        return runBlocking {
            client.post("$server/server/move/") {
                header("Content-Type", "application/json")
                body = MoveRequest(user, dir)
            }
        }
    }
}

fun main(args: Array<String>) {
    if (args.size != 2) {
        System.err.println("usage: ./gradlew run --args=\"NICKNAME SERVER\"")
        return
    }

    val user = args[0]
    val server = args[1]
    val fontConfig = SwingTerminalFontConfiguration.getDefaultOfSize(25)
    var client: Client? = null
    var startState: State = State.WAIT
    val port = if (user == "was") {
        1235
    } else {
        1234
    }
    embeddedServer(io.ktor.server.cio.CIO, port = port) {
        routing {
            post("/state") {
                if (call.request.queryParameters["value"] == "ACTIVE") {
                    System.err.println("SET ACTIVE STATE")
                    client?.state = State.ACTIVE
                    startState = State.ACTIVE
                } else if (call.request.queryParameters["value"] == "WAIT") {
                    System.err.println("SET WAIT STATE")
                    client?.state = State.WAIT
                    startState = State.WAIT
                }
                client?.conditionVariable?.offer(Unit)
                System.err.println("OFFERED")
                call.respondText("OK")
            }
        }
    }.start(wait = false)
    val terminalFactory = DefaultTerminalFactory()
        .setInitialTerminalSize(TerminalSize(20, 23))
        .setTerminalEmulatorFontConfiguration(fontConfig)
    terminalFactory.createTerminal().use { term ->
        val screen = TerminalScreen(term)
        screen.startScreen()
        screen.cursorPosition = null
        HttpClient(CIO){ install(JsonFeature) {
            serializer = KotlinxSerializer(kotlinx.serialization.json.Json {
                ignoreUnknownKeys = true
            })
        }}.use { httpClient ->
            client = Client(user, screen, httpClient, server)
            client?.state = startState
            client?.gameLoop()
        }
    }
}
