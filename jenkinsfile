stages {

        // ---------- STEP 1 : Get code from GitHub ----------
        stage('1. Checkout from Git') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/mohanprasadme/deliveryproject.git'
                    // If repo is PRIVATE add:  credentialsId: 'github-creds'
            }
        }

        // ---------- STEP 2 : Copy code to E:\jenkinsproject ----------
        // Your database, secret key, backups and venv are PROTECTED
        // (they are excluded, so they are never overwritten or deleted).
        stage('2. Copy files to E:\\jenkinsproject') {
            steps {
                bat '''
                @echo off
                if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"

                rem --- Find where manage.py is (repo root OR inside dc_app folder) ---
                set "SRC=%WORKSPACE%"
                if exist "%WORKSPACE%\\dc_app\\manage.py" set "SRC=%WORKSPACE%\\dc_app"
                echo Source folder : %SRC%
                echo Target folder : %DEPLOY_DIR%

                robocopy "%SRC%" "%DEPLOY_DIR%" /MIR /NFL /NDL /NJH /NJS ^
                    /XD .git venv backups staticfiles __pycache__ ^
                    /XF db.sqlite3 secret.key *.pyc Jenkinsfile

                rem robocopy: exit code below 8 means SUCCESS
                if %ERRORLEVEL% GEQ 8 (exit /b 1) else (exit /b 0)
                '''
            }
        }

        // ---------- STEP 3 : Python virtual env + packages (inside E:) ----------
        stage('3. Install packages') {
            steps {
                bat '''
                @echo off
                cd /d "%DEPLOY_DIR%"

                rem Create venv only the first time
                if not exist "venv\\Scripts\\python.exe" (
                    echo Creating virtual environment in %DEPLOY_DIR%\\venv
                    %PYTHON_EXE% -m venv venv || exit /b 1
                )

                call venv\\Scripts\\activate
                python -m pip install --upgrade pip
                pip install -r requirements.txt || exit /b 1
                '''
            }
        }

        // ---------- STEP 4 : Backup DB, migrate, static files ----------
        stage('4. Backup + Migrate + Static') {
            steps {
                bat '''
                @echo off
                cd /d "%DEPLOY_DIR%"
                call venv\\Scripts\\activate

                rem Backup existing database (skipped on very first deploy)
                if exist db.sqlite3 python manage.py backup_db --keep 60

                python manage.py migrate --noinput          || exit /b 1
                python manage.py collectstatic --noinput    || exit /b 1
                '''
            }
        }

        // ---------- STEP 5 : Restart the application ----------
        stage('5. Restart application') {
            steps {
                // These two variables stop Jenkins from killing the server
                // when the build finishes.
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe', 'BUILD_ID=dontKillMe']) {
                    powershell '''
                    $ErrorActionPreference = "Stop"

                    # 1) Stop the old server running on the app port (if any)
                    $old = Get-NetTCPConnection -LocalPort $env:APP_PORT -State Listen -ErrorAction SilentlyContinue
                    if ($old) {
                        $old | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
                        Start-Sleep -Seconds 3
                        Write-Host "Old server stopped."
                    }

                    # 2) Start the new server from E:\\jenkinsproject (hidden window)
                    $exe  = Join-Path $env:DEPLOY_DIR "venv\\Scripts\\waitress-serve.exe"
                    $args = "--listen=0.0.0.0:$($env:APP_PORT) --threads=8 dcproject.wsgi:application"
                    Start-Process -FilePath $exe -ArgumentList $args `
                        -WorkingDirectory $env:DEPLOY_DIR -WindowStyle Hidden `
                        -RedirectStandardOutput (Join-Path $env:DEPLOY_DIR "server.log") `
                        -RedirectStandardError  (Join-Path $env:DEPLOY_DIR "server_error.log")
                    Start-Sleep -Seconds 5

                    # 3) Health check
                    try {
                        $r = Invoke-WebRequest "http://localhost:$($env:APP_PORT)/" -UseBasicParsing -TimeoutSec 15
                        Write-Host "App is UP. HTTP status: $($r.StatusCode)"
                    } catch {
                        # a redirect to login page or 4xx still means the server is alive
                        if ($_.Exception.Response) { Write-Host "App is UP (status $([int]$_.Exception.Response.StatusCode))" }
                        else { throw "App did not start. Check E:\\jenkinsproject\\server_error.log" }
                    }
                    '''
                }
            }
        }
    }

    post {
        success { echo "DEPLOYED OK -> http://localhost:${env.APP_PORT}   (folder: ${env.DEPLOY_DIR})" }
        failure { echo 'DEPLOYMENT FAILED - open Console Output and read the red stage.' }
    }
}
