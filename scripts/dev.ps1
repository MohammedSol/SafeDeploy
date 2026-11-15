<#
.SYNOPSIS
    SafeDeploy — script PowerShell de remplacement pour GNU Make.
    Utilisation : .\scripts\dev.ps1 <cible>

.EXAMPLE
    .\scripts\dev.ps1 up
    .\scripts\dev.ps1 down
    .\scripts\dev.ps1 logs
    .\scripts\dev.ps1 clean
    .\scripts\dev.ps1 help
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "logs", "clean", "help")]
    [string]$Target = "help"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host ""
    Write-Host "SafeDeploy — commandes disponibles :" -ForegroundColor Cyan
    Write-Host "  up     Lance PostgreSQL et MLflow en arrière-plan"
    Write-Host "  down   Arrête les services (conserve les données)"
    Write-Host "  logs   Affiche les logs en continu (Ctrl+C pour quitter)"
    Write-Host "  clean  Arrête les services et supprime les volumes (DESTRUCTIF)"
    Write-Host "  help   Affiche cette aide"
    Write-Host ""
}

switch ($Target) {
    "up" {
        Write-Host "Démarrage des services..." -ForegroundColor Green
        docker compose up -d --remove-orphans
    }
    "down" {
        Write-Host "Arrêt des services (volumes conservés)..." -ForegroundColor Yellow
        docker compose down
    }
    "logs" {
        Write-Host "Affichage des logs (Ctrl+C pour quitter)..." -ForegroundColor Cyan
        docker compose logs -f
    }
    "clean" {
        Write-Host "ATTENTION : suppression des volumes en cours..." -ForegroundColor Red
        $confirmation = Read-Host "Confirmer la suppression des données ? (oui/non)"
        if ($confirmation -eq "oui") {
            docker compose down -v
            Write-Host "Volumes supprimés." -ForegroundColor Red
        } else {
            Write-Host "Annulé." -ForegroundColor Yellow
        }
    }
    default {
        Show-Help
    }
}
